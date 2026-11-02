#!/usr/bin/env python3
"""v5 product controls over real disposable SQLite using an isolated Chrome AXI browser.

No subscription inference, personal profile, phone, scheduler or production service is used.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import uuid

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from day_attendant.service import Assistant
from day_attendant.connected import Connected
from day_attendant.web import LocalServer

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True);parser.add_argument('--skip-controls',action='store_true');parser.add_argument('--skip-layouts',action='store_true');parser.add_argument('--controls-only',action='store_true');parser.add_argument('--controls-script');parser.add_argument('--layout-widths');parser.add_argument('--capture-palettes',action='store_true');args=parser.parse_args()
out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,CHROME_DEVTOOLS_AXI_SESSION='day-v5-'+uuid.uuid4().hex[:10])
for key in ('CHROME_DEVTOOLS_AXI_BROWSER_URL','CHROME_DEVTOOLS_AXI_AUTO_CONNECT','CHROME_DEVTOOLS_AXI_USER_DATA_DIR','CHROME_DEVTOOLS_AXI_PORT'):env.pop(key,None)
def axi(*args,script=None):
    result=subprocess.run(['chrome-devtools-axi',*args],input=script,env=env,text=True,capture_output=True,timeout=90)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    return result.stdout
report={'scope':'Real SQLite + local HTTP + isolated Chrome AXI, no LLM or physical-device evidence','checks':[]}
with tempfile.TemporaryDirectory(prefix='day-v5-ui-') as state:
    app=Assistant(state);board=Connected(app);board.initialize(kind='personal',zone='America/Edmonton')
    def add(title,groups,priority='medium'):
        return board.request('task_add',{'title':title,'groups':groups,'priority':priority},'fixture-'+title)['result']['uuid']
    a=add('Revisar propuesta',['Casa','Trabajo'],'high');b=add('Pagar recibo',['Casa'],'urgent');c=add('Leer notas',['Trabajo','🏠casa'])
    for n in range(20):add('Grupo '+str(n),['Grupo '+str(n)])
    board.request('front_activate',{'uuid':a},'fixture-start');board.request('front_todo',{'uuid':a},'fixture-pause');board.request('task_done',{'uuid':c},'fixture-closed');board.request('dependency_update',{'uuid':a,'dependsOn':[b]},'fixture-dependency')
    server=LocalServer(app,None);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        axi('open',server.origin+'/#session='+server.token)
        if not args.skip_controls:
            script=Path(args.controls_script).resolve() if args.controls_script else ROOT/'scripts/test_v5_ui.js'
            report['controls']=json.loads(axi('run',script=script.read_text()).strip())
            assert report['controls']['passed'],report['controls']
        report['layouts']=[]
        for width in (tuple(map(int,args.layout_widths.split(','))) if args.layout_widths else () if args.skip_layouts or args.controls_only else (360,390,768,1280)):
            axi('resize',str(width),'900')
            metrics=json.loads(axi('run',script="""await page.eval(()=>{if(document.querySelector('#chat-dialog').open)document.querySelector('#chat-close').click()});console.log(JSON.stringify(await page.eval(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,bar:document.querySelector('#appbar').getBoundingClientRect().height,filterHeight:document.querySelector('#group-filters').getBoundingClientRect().height,undoVisible:document.querySelector('#undo').getClientRects().length>0,filterControlsFit:[...document.querySelector('#group-filters').children].filter(n=>n.getClientRects().length).every(n=>{const r=n.getBoundingClientRect(),p=n.parentElement.getBoundingClientRect();return r.left>=p.left-1&&r.right<=p.right+1})}))));""").strip())
            assert metrics['scroll']<=width and metrics['undoVisible'] and metrics['filterHeight']<=36 and metrics['filterControlsFit'],metrics
            report['layouts'].append(metrics)
        if not args.controls_only:
            axi('resize','390','844')
            axi('screenshot',str(out/'mobile.png'))
            axi('resize','1280','900')
            report['themes']=json.loads(axi('run',script="""
    console.log(JSON.stringify(await page.eval(()=>{const rgb=raw=>{const s=raw.trim();if(s.startsWith('#')){let h=s.slice(1);if(h.length===3||h.length===4)h=[...h].map(c=>c+c).join('');return [parseInt(h.slice(0,2),16),parseInt(h.slice(2,4),16),parseInt(h.slice(4,6),16),h.length===8?parseInt(h.slice(6,8),16)/255:1]}
     const match=s.match(/^(rgba?|color)\((.*)\)$/);if(!match)throw Error('Unknown computed color: '+s);let body=match[2],srgb=match[1]==='color';if(srgb){if(!body.startsWith('srgb '))throw Error('Unknown color space: '+s);body=body.slice(5)}const parts=body.split(/[ ,/]+/).filter(Boolean),channels=parts.slice(0,3).map(x=>x.endsWith('%')?parseFloat(x)*2.55:parseFloat(x)*(srgb?255:1));return [...channels,parts[3]===undefined?1:parts[3].endsWith('%')?parseFloat(parts[3])/100:parseFloat(parts[3])]};
     const over=(a,b)=>a.slice(0,3).map((v,i)=>v*a[3]+b[i]*(1-a[3]));
     const lum=a=>a.slice(0,3).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((n,v,i)=>n+v*[.2126,.7152,.0722][i],0);
     const contrast=(a,b)=>(Math.max(lum(a),lum(b))+.05)/(Math.min(lum(a),lum(b))+.05);
     const result=[];for(const palette of ['grafito','papel','oceano'])for(const mode of ['light','dark']){dayTheme.set(mode,palette);document.querySelector('#theme-choice').value=mode;document.querySelector('#palette-choice').value=palette;
     const root=getComputedStyle(document.documentElement),surface=rgb(root.getPropertyValue('--surface')),ink=rgb(root.getPropertyValue('--ink')),muted=rgb(root.getPropertyValue('--muted'));
     const priorities=[...document.querySelectorAll('#board .priority-pill')].filter(n=>['high','medium','urgent'].includes(n.dataset.priority)).map(n=>{const s=getComputedStyle(n),bg=over(rgb(s.backgroundColor),surface);return {priority:n.dataset.priority,contrast:contrast(rgb(s.color),bg)}});
     result.push({palette,mode,ink:contrast(ink,surface),muted:contrast(muted,surface),priorities,colorScheme:root.colorScheme})}return result})))
    """).strip())
            for theme in report['themes']:
                assert theme['ink']>=4.5 and theme['muted']>=4.5 and all(p['contrast']>=4.5 for p in theme['priorities']),theme
            axi('screenshot',str(out/'desktop-oceano-dark.png'))
            # Explicit light survives reload even if the OS selects dark; palette is independently retained.
            axi('run',script="await page.eval(()=>{dayTheme.set('light','papel');location.reload()});await page.wait(400);console.log('reloaded')")
            saved=json.loads(axi('run',script="console.log(JSON.stringify(await page.eval(()=>({theme:document.documentElement.dataset.theme,palette:document.documentElement.dataset.palette,mode:document.querySelector('#theme-choice').value,scheme:getComputedStyle(document.documentElement).colorScheme,undo:!document.querySelector('#undo').disabled}))));").strip())
            assert saved=={'theme':'light','palette':'papel','mode':'light','scheme':'light','undo':True},saved
            report['persisted']=saved
            console=axi('console','--type','error');report['console']=console
            assert ' [error] ' not in console,console
        if args.capture_palettes:
            axi('resize','1280','900')
            axi('run',script="await page.eval(()=>{document.querySelector('#locale-choice').value='es';document.querySelector('#locale-choice').dispatchEvent(new Event('change'));document.querySelector('[data-filter=\"*\"]').click()});console.log('ready')")
            for palette in ('grafito','papel','oceano'):
                for mode in ('light','dark'):
                    script="await page.eval(()=>{document.querySelector('#theme-choice').value="+json.dumps(mode)+";document.querySelector('#palette-choice').value="+json.dumps(palette)+";document.querySelector('#palette-choice').dispatchEvent(new Event('change'))});console.log('ready')"
                    axi('run',script=script);axi('screenshot',str(out/(palette+'-'+mode+'.png')))
            report['paletteScreens']=6
        report['passed']=True
    except BaseException as error:
        report['passed']=False;report['error']=str(error);raise
    finally:
        (out/'result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        axi('stop');server.shutdown();thread.join(5);server.server_close();server.pool.shutdown(wait=True)
print(json.dumps({'passed':report.get('passed'),'report':str(out/'result.json')}))
