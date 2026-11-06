#!/usr/bin/env python3
"""Selected Markdown download against disposable SQLite and a controlled model."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import uuid

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from day_attendant.service import Assistant
from day_attendant.web import LocalServer
from test_conversation import ChatFixture

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out', required=True)
out = Path(parser.parse_args().out).resolve()
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, CHROME_DEVTOOLS_AXI_SESSION='record-' + uuid.uuid4().hex[:10])
for key in ('CHROME_DEVTOOLS_AXI_BROWSER_URL', 'CHROME_DEVTOOLS_AXI_AUTO_CONNECT', 'CHROME_DEVTOOLS_AXI_PORT'):
    env.pop(key, None)

def axi(*args, script=None):
    result = subprocess.run(['chrome-devtools-axi', *args], input=script, text=True,
                            capture_output=True, env=env, timeout=60)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout

with tempfile.TemporaryDirectory(prefix='day-record-') as temp:
    profile = Path(temp) / 'chrome' / 'Default'
    profile.mkdir(parents=True)
    downloads = out / 'downloads'
    downloads.mkdir(exist_ok=True)
    (profile / 'Preferences').write_text(json.dumps({'download': {
        'default_directory': str(downloads), 'prompt_for_download': False}}))
    env['CHROME_DEVTOOLS_AXI_USER_DATA_DIR'] = str(profile.parent)
    app = Assistant(str(Path(temp) / 'state'))
    bridge = ChatFixture({'message': 'PRIVATE_OLD_REPLY', 'uncertainties': [], 'intent': None})
    server = LocalServer(app, bridge)
    server.catalogs = {'codex': [], 'claude': []}
    server.board.initialize(kind='personal', zone='UTC')
    server.board.request('task_add', {'title': 'PRIVATE_TASK'}, 'private-task')
    server.chat.submit('PRIVATE_HISTORY', 'old')
    server.chat.run('old')
    selected = '# Registro 🚀\n\nCafé, español y 日本語.\n\nOmitir esta línea.'
    bridge.output['message'] = selected
    server.chat.submit('Prepara un registro Markdown de los puntos acordados.', 'record')
    server.chat.run('record')
    bridge.output['message'] = ('# Solicitud: sincronización\n\nClasificación: carencia\n\n'
        '## Contexto\nConsultar tareas desde dos dispositivos.\n\n'
        '## Flujo deseado\n1. Abrir ambos dispositivos.\n2. Consultar los mismos cambios.\n\n'
        '## Resultado actual\nNo hay sincronización automática documentada.\n\n'
        '## Resultado esperado\nSincronizar los cambios.\n\n'
        '## Datos pendientes\nVersión y dispositivos: no proporcionados.')
    server.chat.submit('Redacta una solicitud de sincronización entre dispositivos.', 'support')
    server.chat.run('support')
    before = server.board.snapshot()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        axi('open', server.origin + '/#session=' + server.token)
        checks = axi('run', script=(ROOT / 'scripts/test_record_export_ui.mjs').read_text())
        for width, height in ((1440, 1000), (390, 844)):
            axi('resize', str(width), str(height))
            for theme in ('light', 'dark'):
                axi('eval', f"() => dayTheme.set('{theme}')")
                axi('screenshot', str(out / f'{width}-{theme}.png'))
                result = axi('eval', "() => {const d=document.getElementById('record-export-dialog'),r=d.getBoundingClientRect();return JSON.stringify({fits:r.x>=0&&r.right<=innerWidth&&r.y>=0&&r.bottom<=innerHeight,noOverflow:d.scrollWidth<=d.clientWidth})}")
                assert 'true' in result and 'false' not in result, result
        axi('run', script="""
await page.fill('#record-export-name','registro-compartido.md');
await page.eval(()=>{window.showSaveFilePicker=undefined});
await page.eval(()=>document.querySelector('#record-export-dialog [type=submit]').focus());
await page.press('Enter');
console.log(JSON.stringify(await page.eval(()=>document.getElementById('record-export-status').textContent)));
""")
        downloaded = downloads / 'registro-compartido.md'
        deadline = time.monotonic() + 10
        while not downloaded.exists() and time.monotonic() < deadline:
            time.sleep(.1)
        assert downloaded.exists(), list(downloads.iterdir())
        assert downloaded.read_text() == '# Sólo café 🚀\n\n日本語: 確認済み\n', list(downloads.iterdir())
        assert server.board.snapshot()['revision'] == before['revision']
        (out / 'report.json').write_text(json.dumps({'checks': checks, 'download': downloaded.name,
                                                    'content_exact': True, 'state_unchanged': True}, ensure_ascii=False, indent=2))
        print('Selected record download, errors, cancellation, Unicode and four visual views passed.')
    finally:
        try:
            axi('stop')
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
