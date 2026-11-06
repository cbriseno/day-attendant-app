"""Read app help from the shipped docs and UI definitions, never a second catalog."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS = ('README.md', 'docs/daily-operation.md', 'docs/chat-contract.md')


def app_help():
    # Read on each turn so source edits are visible without a generated artifact
    # or a cache to invalidate. These are public app sources.
    documents = {name: (ROOT / name).read_text(encoding='utf-8') for name in DOCUMENTS}
    ui = ROOT / 'day_attendant/ui'
    sources = {'index.html': (ui / 'index.html').read_text(encoding='utf-8').split('<body', 1)[1]}
    for name in ('interface.js', 'daily.js', 'ordering.js'):
        lines = (ui / name).read_text(encoding='utf-8').splitlines()
        selected = set()
        for i, line in enumerate(lines):
            if (name == 'ordering.js' or re.search(
                    r'keydown|\be\.key\b|setTaskView|taskView\s*===|settings-open|capture-open|preferenceIds|'
                    r'function (?:focus\w*|chainLanes|groupLanes|render|buildSettings|mountPreferences|parkPreferences)\(', line)):
                selected.update(range(max(0, i - 2), min(len(lines), i + 4)))
        sources[name] = '\n'.join(f'{i + 1}: {lines[i]}' for i in sorted(selected))
    # Include real captions for referenced controls, including later catalog
    # additions. Keep both languages; answers follow the human's language.
    keys = set(re.findall(r'''['"]([\w-]+)['"]''', '\n'.join(sources.values())))
    catalog = (ui / 'locales.js').read_text(encoding='utf-8')
    captions = {}
    for quoted, bare, value in re.findall(
            r'''(?:"([\w-]+)"|(\w+))\s*:\s*("(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')''', catalog):
        key = quoted or bare
        referenced = key in keys or any(key.startswith(k) for k in keys if k.endswith('_'))
        if referenced and value not in captions.setdefault(key, []):
            captions[key].append(value)
    return {'documents': documents, 'uiDefinitions': sources, 'captions': captions,
            'scope': 'Public shipped documentation and UI source excerpts, not a live browser inspection. '
                     'Use capabilities.functions for executable actions and capabilities.execution for current availability. '
                     'UI definitions describe controls, not the human\'s current view, focus or browser preferences.'}
