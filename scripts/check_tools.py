"""Read-only inventory of tools needed by Day Attendant."""
import platform
import shutil
import subprocess
import sys


def tool(name, minimum, factory, impact):
    path = shutil.which(name)
    version = 'missing'
    if path:
        try:
            result = subprocess.run([path, '--version'], capture_output=True, text=True, timeout=3)
            version = (result.stdout or result.stderr).strip().splitlines()[0] or 'version unknown'
        except (OSError, subprocess.SubprocessError, IndexError):
            version = 'version unknown'
    print(f'Optional {name}: {version}; minimum {minimum}; macOS {factory}; without it: {impact}')


def main():
    ready = sys.version_info >= (3, 11)
    print(f'Required Python: {platform.python_version()}; minimum 3.11; macOS availability not assured; without it: core unavailable')
    try:
        import sqlite3
        ok = sqlite3.sqlite_version_info >= (3, 35, 0)
        ready &= ok
        print(f'Required SQLite: {sqlite3.sqlite_version}; minimum 3.35; bundled with Python, macOS availability not assured; without it: storage unavailable')
    except ImportError:
        ready = False
        print('Required SQLite: missing; minimum 3.35; macOS availability not assured; without it: storage unavailable')
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo('UTC')
        print('Required zoneinfo and UTC data: available; minimum Python 3.11; macOS normally supplies timezone data; missing selected zones cannot be used')
    except (ImportError, KeyError):
        ready = False
        print('Required zoneinfo and UTC data: missing; minimum Python 3.11; macOS normally supplies timezone data; without it: timezone operation unavailable')
    for args in [('node', '18 for optional tests', 'not normally supplied', 'optional ordering test'), ('codex', 'protocol baseline 0.164.0', 'not normally supplied', 'Codex inference'), ('claude', 'protocol baseline 2.1.312', 'not normally supplied', 'Claude inference'), ('osascript', 'unknown', 'normally supplied', 'macOS notifications'), ('launchctl', 'unknown', 'normally supplied', 'macOS scheduling')]:
        tool(*args)
    print('Optional browser: version unknown; minimum modern browser (unknown); macOS normally supplies Safari; without it: UI unavailable')
    print('READY' if ready else 'MISSING required tools or capabilities')
    return 0 if ready else 1


if __name__ == '__main__':
    sys.exit(main())
