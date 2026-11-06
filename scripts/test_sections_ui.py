#!/usr/bin/env python3
"""Persistent section folding with real disposable SQLite/HTTP and isolated Chrome AXI."""
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

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from day_attendant.connected import Connected
from day_attendant.service import Assistant
from day_attendant.web import LocalServer
from test_connected import ReviewFixture

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', required=True)
parser.add_argument('--screens-only', action='store_true')
args = parser.parse_args()
out = Path(args.out).resolve()
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, CHROME_DEVTOOLS_AXI_SESSION='day-sections-' + uuid.uuid4().hex[:10])
for key in ('CHROME_DEVTOOLS_AXI_BROWSER_URL', 'CHROME_DEVTOOLS_AXI_AUTO_CONNECT',
            'CHROME_DEVTOOLS_AXI_USER_DATA_DIR', 'CHROME_DEVTOOLS_AXI_PORT'):
    env.pop(key, None)


def axi(*command, script=None):
    result = subprocess.run(['chrome-devtools-axi', *command], input=script, env=env,
                            text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


with tempfile.TemporaryDirectory(prefix='day-sections-ui-') as state:
    app = Assistant(state)
    bridge = ReviewFixture()
    board = Connected(app, bridge)
    board.initialize(kind='personal', zone='UTC')

    def apply(action, payload, key):
        return board.request(action, payload, key, expected_revision=board.snapshot()['revision'])

    ids = [apply('task_add', {'title': f'Synthetic responsibility {i + 1}',
                            'group': 'Example/Subgroup' if i % 2 else 'Example'}, f'seed-{i}')['result']['uuid']
           for i in range(30)]
    apply('dependency_update', {'uuid': ids[-1], 'dependsOn': [ids[0]]}, 'link')
    apply('task_done', {'uuid': ids[-2]}, 'closed')
    apply('task_cancel', {'uuid': ids[-3]}, 'cancel')
    apply('task_update', {'uuid': ids[-4], 'nextUp': True}, 'next')
    now = datetime.now(timezone.utc)
    apply('event_add', {'title': 'Synthetic meeting', 'start': (now + timedelta(hours=1)).isoformat(),
                       'end': (now + timedelta(hours=2)).isoformat()}, 'event')
    board.request('organize_capture', {'uuid': ids[1], 'original': 'Synthetic responsibility 2',
                  'expectedTitle': 'Synthetic responsibility 2', 'tasks': [
                      {'title': 'Synthetic organized task', 'notes': 'Synthetic notes', 'groups': ['Example'], 'after': []}]},
                  'organization', origin='assistant', expected_revision=board.snapshot()['revision'])
    apply('continuity_update', {'uuid': ids[0], 'checklist': [{'id': f'item-{i}', 'text': f'Synthetic step {i + 1}', 'done': False} for i in range(30)]}, 'checklist')
    apply('related_update', {'uuid': ids[0], 'relatedTo': ids[2:9]}, 'related')
    revision = board.snapshot()['revision']
    server = LocalServer(app, bridge)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    report = {}
    try:
        axi('open', server.origin + '/#session=' + server.token)
        axi('run', script="await page.wait('[data-state=todo] [data-section-fold]');")
        if not args.screens_only:
            report['behavior'] = json.loads(axi('run', script=(ROOT / 'scripts/test_sections_ui.mjs').read_text()).strip().splitlines()[-1])
        for width, height in ((1440, 1000), (390, 844)):
            axi('resize', str(width), str(height))
            axi('run', script="await page.eval(()=>{document.querySelector('#chat-close').click()});")
            for theme in ('light', 'dark'):
                axi('run', script=f"await page.eval(()=>{{const e=document.querySelector('#theme-choice');e.value='{theme}';e.dispatchEvent(new Event('change',{{bubbles:true}}));document.querySelector('#list-view').click();const b=document.querySelector('[data-state=todo] [data-section-fold]');if(b.getAttribute('aria-expanded')==='true')b.click();scrollTo(0,0)}});")
                axi('run', script="await page.eval(()=>document.querySelector('[data-state=todo] [data-section-fold]').focus());await page.press('Enter');await page.eval(()=>{if(document.querySelector('[data-state=todo] [data-section-fold]').getAttribute('aria-expanded')!=='true')throw Error('Viewport keyboard expansion')});await page.press('Space');await page.eval(()=>{if(document.querySelector('[data-state=todo] [data-section-fold]').getAttribute('aria-expanded')!=='false')throw Error('Viewport keyboard fold');scrollTo(0,0)});")
                axi('screenshot', str(out / f'today-folded-{width}-{theme}.png'))
                axi('run', script="await page.click('[data-state=todo] [data-section-fold]');")
                axi('screenshot', str(out / f'today-open-{width}-{theme}.png'))
                axi('run', script="await page.click('[data-state=todo] [data-section-fold]');await page.click('#group-view');")
                axi('screenshot', str(out / f'groups-{width}-{theme}.png'))
                axi('run', script="await page.click('#settings-open');")
                axi('screenshot', str(out / f'settings-{width}-{theme}.png'))
                axi('run', script="await page.eval(()=>{document.querySelector('#settings-dialog').close();if(document.documentElement.scrollWidth>innerWidth)throw Error('Horizontal overflow');const b=document.querySelector('#board .fold');if(innerWidth<600&&b.getBoundingClientRect().height<34)throw Error('Touch target too small')});")
                axi('run', script="await page.click('#settings-open');await page.click('[data-org-history]');await page.wait('details.org-item');await page.eval(()=>document.querySelector('details.org-item').open=true);")
                axi('screenshot', str(out / f'history-{width}-{theme}.png'))
                axi('run', script="await page.click('details.org-item>summary');")
                axi('screenshot', str(out / f'history-folded-{width}-{theme}.png'))
                axi('run', script="await page.eval(()=>{document.querySelector('#org-dialog').close();document.querySelector('#settings-dialog')?.close()});")
                for view in ('board', 'chains', 'focus'):
                    axi('run', script=f"await page.click('#{view}-view');await page.eval(()=>scrollTo(0,0));")
                    axi('screenshot', str(out / f'{view}-{width}-{theme}.png'))

        assert board.snapshot()['revision'] == revision, 'Presentation controls must not mutate profile data'
        report['console'] = axi('console')
        report['passed'] = True
    except BaseException as error:
        report['error'] = str(error)
        raise
    finally:
        (out / 'sections-report.json').write_text(json.dumps(report, indent=2) + '\n')
        server.shutdown()
        thread.join(5)
        server.server_close()
        server.pool.shutdown(wait=True)
        axi('stop')
    print(json.dumps(report))
