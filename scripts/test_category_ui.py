#!/usr/bin/env python3
"""Category controls against synthetic SQLite/HTTP and isolated Chrome AXI."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import uuid

ROOT=Path(__file__).resolve().parent.parent
sys.path[:0]=[str(ROOT),str(ROOT/'tests')]
from day_attendant import proactive
from day_attendant.connected import Connected
from day_attendant.profiles import configure
from day_attendant.service import Assistant
from day_attendant.web import LocalServer
from test_connected import ReviewFixture

parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True)
out=Path(parser.parse_args().out).resolve();out.mkdir(parents=True,exist_ok=True)
env=dict(os.environ,CHROME_DEVTOOLS_AXI_SESSION='day-category-'+uuid.uuid4().hex[:10])
for key in ('CHROME_DEVTOOLS_AXI_BROWSER_URL','CHROME_DEVTOOLS_AXI_AUTO_CONNECT','CHROME_DEVTOOLS_AXI_USER_DATA_DIR','CHROME_DEVTOOLS_AXI_PORT'):
    env.pop(key,None)
def axi(*command,script=None):
    result=subprocess.run(['chrome-devtools-axi',*command],input=script,env=env,text=True,capture_output=True,timeout=60)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    return result.stdout

with tempfile.TemporaryDirectory(prefix='day-category-ui-') as state:
    now=datetime.now(timezone.utc)
    app=Assistant(state,clock=lambda:now);bridge=ReviewFixture();board=Connected(app,bridge)
    board.initialize(kind='personal',zone='UTC');configure(app,{'locale':'es'},'locale');proactive.configure(app.store,{'enabled':False})
    def apply(action,payload,key):return board.request(action,payload,key,expected_revision=board.snapshot()['revision'])
    for i,(group,priority) in enumerate([('Release','low'),('Release','urgent'),('Security team','high'),('Experiments','medium'),('Release/API','high'),('', 'low')]):
        now+=timedelta(seconds=1)
        p=apply('task_add',{'title':f'Synthetic task {i+1}','group':group,'priority':priority},f'seed-{i}')
        if i==0:
            apply('front_activate',{'uuid':p['result']['uuid']},'active')
            apply('continuity_update',{'uuid':p['result']['uuid'],'blockReason':'Synthetic outside dependency'},'block')
    server=LocalServer(app,bridge);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    report={}
    try:
        axi('open',server.origin+'/#session='+server.token)
        report['behavior']=json.loads(axi('run',script=(ROOT/'scripts/test_category_ui.mjs').read_text()).strip().splitlines()[-1])
        for width,height in ((1440,1000),(390,844)):
            axi('resize',str(width),str(height))
            for theme in ('light','dark'):
                axi('run',script=f"await page.eval(()=>{{document.querySelector('#chat-close').click();const e=document.querySelector('#theme-choice');e.value='{theme}';e.dispatchEvent(new Event('change',{{bubbles:true}}));document.querySelector('#group-view').click();const o=document.querySelector('#order-then');o.value='priority';o.dispatchEvent(new Event('change',{{bubbles:true}}));const toolbar=document.querySelector('.toolbar');toolbar.classList.add('options-open');scrollTo(0,0);if(document.documentElement.scrollWidth>innerWidth)throw Error('Horizontal overflow');for(const e of document.querySelectorAll('.category-tools select,.category-tools button'))if(e.getBoundingClientRect().height<36)throw Error('Small category control')}});")
                axi('screenshot',str(out/f'categories-{width}-{theme}.png'))
        report['console']=axi('console');report['passed']=True
    except BaseException as error:
        report['error']=str(error);raise
    finally:
        (out/'category-report.json').write_text(json.dumps(report,indent=2)+'\n')
        server.shutdown();thread.join(5);server.server_close();server.pool.shutdown(wait=True);axi('stop')
    print(json.dumps(report))
