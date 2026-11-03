#!/usr/bin/env python3
"""Anonymize regression fixtures via the existing Chrome AXI/SQLite UI harness.

Run: python3 -B scripts/test_anonymize_ui.py --out /tmp/day-anonymize-proof
No browser libraries or Python dependencies are installed.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import uuid

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from day_attendant.connected import Connected
from day_attendant.conversation import Conversation
from day_attendant.service import Assistant
from day_attendant.web import LocalServer, Handler, ASSETS
from day_attendant.profiles import configure
from test_conversation import ChatFixture

# Inject a self-hosted probe in this fixture only, before the body is parsed. It
# survives reload as a fresh probe and samples every changed frame, including the
# first render from a tab whose sessionStorage already enables anonymization.
PROBE = r"""
window.anonymizeProbe={frames:0,leaks:[]};let changed=true;
new MutationObserver(()=>{changed=true}).observe(document.documentElement,{subtree:true,childList:true,attributes:true,characterData:true});
function probeFrame(){const body=document.body;if(body&&changed){anonymizeProbe.frames++;changed=false;
 if(sessionStorage.getItem('day-attendant-anonymize')==='1'&&getComputedStyle(body).visibility!=='hidden'){
  const walker=document.createTreeWalker(body,NodeFilter.SHOW_ELEMENT|NodeFilter.SHOW_TEXT);let exposed=false;
  while(walker.nextNode()){const n=walker.currentNode;if(n.nodeType===3){if(!n.parentElement?.closest('script,style')&&n.data.includes('CANARY_'))exposed=true}
   else{for(const a of ['title','aria-label','alt','placeholder','value'])if(n.getAttribute(a)?.includes('CANARY_'))exposed=true;if('value'in n&&String(n.value).includes('CANARY_'))exposed=true}}
  if(exposed)anonymizeProbe.leaks.push(anonymizeProbe.frames);
 }}requestAnimationFrame(probeFrame)}requestAnimationFrame(probeFrame);
"""

class ProbeHandler(Handler):
    def do_GET(self):
        if self.path == '/anonymize-probe.js':
            self.reply(200, PROBE.encode(), 'text/javascript; charset=utf-8')
        elif self.path in ('/', '/index.html'):
            html = (ASSETS / 'index.html').read_text().replace(
                '<script src="/anonymize-boot.js"></script>',
                '<script src="/anonymize-boot.js"></script><script src="/anonymize-probe.js"></script>',
            )
            self.reply(200, html.encode(), 'text/html; charset=utf-8')
        else:
            super().do_GET()

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', required=True)
args = parser.parse_args()
out = Path(args.out).resolve()
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, CHROME_DEVTOOLS_AXI_SESSION='day-anonymize-' + uuid.uuid4().hex[:10])
for key in ('CHROME_DEVTOOLS_AXI_BROWSER_URL', 'CHROME_DEVTOOLS_AXI_AUTO_CONNECT', 'CHROME_DEVTOOLS_AXI_USER_DATA_DIR', 'CHROME_DEVTOOLS_AXI_PORT'):
    env.pop(key, None)

def axi(*command, script=None):
    result = subprocess.run(['chrome-devtools-axi', *command], input=script, env=env, text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout

with tempfile.TemporaryDirectory(prefix='day-anonymize-') as state:
    app = Assistant(state, clock=lambda: datetime(2026, 11, 2, 12, tzinfo=timezone.utc))
    bridge = ChatFixture({'message': 'CANARY_ASSISTANT_43 **CANARY_MARKDOWN_44**', 'uncertainties': [], 'intent': None})
    board = Connected(app, bridge)
    board.initialize(kind='personal', zone='UTC')
    configure(app, {'name': 'CANARY_PROFILE_200'}, 'profile-fixture')
    def apply(action, payload, key):
        return board.request(action, payload, key, expected_revision=board.snapshot()['revision'])
    for i in range(4):
        uid = apply('task_add', {'title': f'CANARY_TITLE_{i} ' + ['Prepare a detailed project update for tomorrow', 'Review the quarterly notes with the team', 'Call the repair shop about the appointment', 'Organize remaining items'][i], 'group': 'CANARY_GROUP_7', 'priority': ['high', 'medium', 'low', 'high'][i], 'due': '2026-12-09T14:30:00Z', 'source': 'chat', 'person': 'CANARY_PERSON_201', 'reference': 'CANARY_REFERENCE_202', 'observed_at': '2026-11-01T12:00:00Z'}, f'add-{i}')['result']['uuid']
        apply('continuity_update', {'uuid': uid, 'context': f'CANARY_CONTEXT_{i}', 'next': f'CANARY_NEXT_{i}', 'remainingMinutes': 17}, f'continuity-{i}')
        if i == 3:
            apply('task_done', {'uuid': uid}, 'close-3')
    apply('event_add', {'title': 'CANARY_EVENT_203', 'start': '2026-12-09T14:30:00Z', 'end': '2026-12-09T15:30:00Z'}, 'calendar-fixture')
    chat = Conversation(board)
    chat.submit('CANARY_USER_42', 'chat-fixture')
    chat.run('chat-fixture')
    server = LocalServer(app, bridge)
    server.RequestHandlerClass = ProbeHandler
    server.catalogs = {'codex': [], 'claude': []}
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    report = {}
    before = board.snapshot()
    try:
        axi('open', server.origin + '/#session=' + server.token)
        report['checks'] = []
        for width, height in ((1440, 1000), (390, 844)):
            axi('resize', str(width), str(height))
            result = json.loads(axi('run', script=(ROOT / 'scripts/test_anonymize_ui.mjs').read_text()).strip().splitlines()[-1])
            report['checks'].append({'viewport': [width, height], **result})
        report['mobile'] = []
        for width in (1280, 900, 768, 600, 480, 390, 360):
            axi('resize', str(width), '900')
            result = json.loads(axi('run', script=(ROOT / 'scripts/test_mobile_layout.mjs').read_text()).strip().splitlines()[-1])
            report['mobile'].append({'width': width, **result})
        report['reload'] = json.loads(axi('run', script="await page.eval(async()=>{await dayAnonymize.setActive(true)});await page.eval(()=>location.reload());await page.wait('[data-task-id]');console.log(JSON.stringify(await page.eval(async()=>{await dayAnonymize.ready;if(!dayAnonymize.active)throw Error('Session reload off');for(const e of document.querySelectorAll('.task-title,#profile-badge,.message-content'))if(e.textContent.includes('CANARY_'))throw Error('Reload leaked '+e.outerHTML+' hidden='+document.documentElement.hasAttribute('data-anon-loading'));if(!anonymizeProbe.frames||anonymizeProbe.leaks.length)throw Error('Reload visible frame canary '+JSON.stringify(anonymizeProbe));await dayAnonymize.setActive(false);return {reload:true,probe:anonymizeProbe}})));").strip().splitlines()[-1])
        report['console'] = axi('console')
        assert ' [error] ' not in report['console'], report['console']
        assert board.snapshot()['revision'] == before['revision'], 'Anonymizing must not save changes'
        report['passed'] = True
    except BaseException as error:
        report['passed'] = False
        report['error'] = str(error)
        raise
    finally:
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        server.shutdown()
        thread.join(5)
        server.server_close()
        server.pool.shutdown(wait=True)
        axi('stop')
        print(json.dumps(report))
