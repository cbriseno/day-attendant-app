"""The same standard-library SQLite task store on Linux and macOS.

The coordinator owns policy and its journal. This store atomically persists one
participant at a time so an interrupted operation can compare before/after rows.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import threading
import uuid

from .errors import AssistantError
from .store import release, reuse
from .timeutil import parse, stamp, wire, utcnow

# Public priority names, most pressing first, and their stored codes. Schema 2 adds
# urgent; high, medium and low keep the codes every earlier profile already uses.
PRIORITIES = {'urgent': 'U', 'high': 'H', 'medium': 'M', 'low': 'L'}


def canonical(row):
    if row is None:
        return None
    result = {k: v for k, v in row.items() if k not in ('id', 'urgency', 'modified')}
    if result.get('depends'):
        result['depends'] = sorted(result['depends'])
    else:
        result.pop('depends', None)
    return result


# Schema 1 holds only high, medium and low. Schema 2 has the same rows and also admits
# urgent. Schema 3 adds list memberships and the permanent alias registry; older releases refuse it.
SCHEMA = 3


class TaskStore:
    backend = 'python-sqlite'
    storage_format = 2
    storage_files = ('assistant.sqlite3', 'tasks.sqlite3')

    def __init__(self, store):
        self.database = store.path / 'tasks.sqlite3'
        self.idle, self.idle_lock = [], threading.Lock()
        self.decoded = {}
        with store.lock():
            if not self.database.exists() and (store.path / 'taskwarrior').exists():
                raise AssistantError('task_migration_required',
                    'This profile still uses Taskwarrior. Stop its service and run profile migrate; no tasks were replaced.')
            existed = self.database.exists()
            fd = os.open(self.database, os.O_CREAT | os.O_RDWR, 0o600)
            os.close(fd)
            with self.connect(write=True) as con:
                version = con.execute('PRAGMA user_version').fetchone()[0]
                if not existed:
                    con.execute('CREATE TABLE tasks(uuid TEXT PRIMARY KEY NOT NULL, data TEXT NOT NULL)')
                    con.execute(f'PRAGMA user_version={SCHEMA}')
                    con.execute('CREATE TABLE aliases(number INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT UNIQUE NOT NULL)')
                elif version not in (1, 2, SCHEMA):
                    raise AssistantError('unsupported_task_schema', 'The task store has an unsupported schema; no tasks were replaced.')
            self.database.chmod(0o600)
            if self.schema()>=3:self.validate_aliases()

    @contextmanager
    def connect(self, write=False):
        try:
            # As in the auxiliary store, a committed connection is reused by the next context.
            con = reuse(self)
            if con is None:
                con = sqlite3.connect(self.database, timeout=10, check_same_thread=False)
            settled = False
            try:
                con.execute('PRAGMA busy_timeout=10000')
                if write:
                    con.execute('BEGIN IMMEDIATE')
                with con:
                    yield con
                settled = not con.in_transaction
            finally:
                release(self, con, settled)
        except sqlite3.Error as error:
            raise AssistantError('task_storage_error', 'The SQLite task operation failed; inspect recovery before retrying.') from error

    @staticmethod
    def validate(row):
        if not isinstance(row, dict):
            raise AssistantError('invalid_task_record', 'A task record must be an object.')
        try:
            if str(uuid.UUID(row['uuid'])) != row['uuid']:
                raise ValueError('uuid')
            if not isinstance(row['description'], str) or not row['description'].strip():
                raise ValueError('description')
            if row.get('status') not in ('pending', 'completed', 'deleted', 'recurring'):
                raise ValueError('status')
            for field in ('entry', 'due', 'wait', 'start', 'end', 'lastActive', 'groupChanged'):
                if field in row:
                    parse(row[field])
            if row.get('priority') not in (None, *PRIORITIES.values()):
                raise ValueError('priority')
            groups = row.get('project', '')
            if not isinstance(groups, str) and (not isinstance(groups, list) or any(not isinstance(g, str) or not g.strip() or len(g)>120 for g in groups)):
                raise ValueError('project')
            refs = row.get('depends', [])
            if not isinstance(refs, list) or len(refs) != len(set(refs)):
                raise ValueError('depends')
            for ref in refs:
                if str(uuid.UUID(ref)) != ref:
                    raise ValueError('dependency uuid')
            json.dumps(row, allow_nan=False)
        except (KeyError, TypeError, ValueError, AttributeError, AssistantError) as error:
            raise AssistantError('invalid_task_record', 'A stored task has invalid identity, fields, or dates.') from error
        return canonical(row)

    def version(self):
        return '1'

    def schema(self):
        with self.connect() as con:
            return con.execute('PRAGMA user_version').fetchone()[0]

    def require_urgent(self):
        if self.schema() < 2:
            raise AssistantError('task_upgrade_required',
                'This profile has not been upgraded for the urgent priority yet. Restart its service or run profile upgrade; nothing was changed.')

    def upgrade(self):
        """Atomic task migration, after the coordinator's verified coherent backup.

        Aliases are an append-only registry. They stay reserved for retired tasks.
        Existing alias assignments survive retries and mixed schema fixtures.
        """
        with self.connect(write=True) as con:
            if con.execute('PRAGMA user_version').fetchone()[0] >= SCHEMA:
                return
            con.execute('CREATE TABLE IF NOT EXISTS aliases(number INTEGER PRIMARY KEY AUTOINCREMENT, uuid TEXT UNIQUE NOT NULL)')
            rows = [self._decode(uid, data) for uid, data in con.execute('SELECT uuid,data FROM tasks')]
            for row in sorted(rows, key=lambda r: (stamp(parse(r['entry'])) if r.get('entry') else '', r['uuid'])):
                con.execute('INSERT OR IGNORE INTO aliases(uuid) VALUES(?)', (row['uuid'],))
                if isinstance(row.get('project'), str):
                    if row['project']:
                        row['project'] = [row['project']]
                    else:
                        row.pop('project')
                    self.validate(row)  # Reject unrepresentable legacy data before committing any row.
                    con.execute('UPDATE tasks SET data=? WHERE uuid=?', (json.dumps(row, ensure_ascii=False), row['uuid']))
            entries=con.execute('SELECT number,uuid FROM aliases').fetchall()
            if {uid for _,uid in entries}!={r['uuid'] for r in rows} or any(type(n) is not int or n<=0 for n,_ in entries):
                raise AssistantError('invalid_task_record','The legacy alias registry needs inspection; migration was rolled back.')
            con.execute(f'PRAGMA user_version={SCHEMA}')

    def aliases(self):
        if self.schema() < 3:
            return {}
        with self.connect() as con:
            return {uid: number for number, uid in con.execute('SELECT number,uuid FROM aliases')}

    def validate_aliases(self):
        with self.connect() as con:
            entries=con.execute('SELECT number,uuid FROM aliases').fetchall()
            known={r[0] for r in con.execute('SELECT uuid FROM tasks')}
        if (len(entries)!=len(known) or {uid for _,uid in entries}!=known
                or any(type(n) is not int or n<=0 for n,_ in entries)
                or len({n for n,_ in entries})!=len(entries)):
            raise AssistantError('invalid_task_record','Permanent task aliases do not match the task registry.')

    def rows(self):
        with self.connect() as con:
            records = con.execute('SELECT uuid,data FROM tasks ORDER BY rowid').fetchall()
        return [self._decode(uid, data) for uid, data in records]

    def _decode(self, uid, data):
        # The same stored text always validates the same, so each version of a row is checked once.
        known = self.decoded.get(uid)
        if known is None or known[0] != data:
            try:
                row = self.validate(json.loads(data))
                if row['uuid'] != uid:
                    raise ValueError('identity mismatch')
            except (ValueError, AssistantError) as error:
                raise AssistantError('invalid_task_record', 'The SQLite task record failed validation.') from error
            known = self.decoded[uid] = (data, row)
        row = dict(known[1])
        if 'depends' in row:
            row['depends'] = list(row['depends'])
        if isinstance(row.get('project'), list):
            row['project'] = list(row['project'])
        return row

    def get(self, uid):
        with self.connect() as con:
            row = con.execute('SELECT data FROM tasks WHERE uuid=?', (uid,)).fetchone()
        return self._decode(uid, row[0]) if row else None

    def create(self, row):
        value = self.validate(dict({'status': 'pending', 'entry': wire(stamp(utcnow()))}, **row))
        with self.connect(write=True) as con:
            old = con.execute('SELECT data FROM tasks WHERE uuid=?', (value['uuid'],)).fetchone()
            if old:
                if self._decode(value['uuid'], old[0]) == value:
                    return
                raise AssistantError('external_conflict', 'A different task already has this UUID; no task was overwritten.')
            if self.schema() >= 3:
                con.execute('INSERT OR IGNORE INTO aliases(uuid) VALUES(?)', (value['uuid'],))
            con.execute('INSERT INTO tasks VALUES(?,?)', (value['uuid'], json.dumps(value, ensure_ascii=False)))

    def patch(self, uid, changes):
        if 'uuid' in changes or any(k in changes for k in ('id', 'urgency', 'modified')):
            raise AssistantError('invalid_task_record', 'Task identity and derived fields cannot be patched.')
        with self.connect(write=True) as con:
            old = con.execute('SELECT data FROM tasks WHERE uuid=?', (uid,)).fetchone()
            if not old:
                raise AssistantError('task_not_found', 'The task does not exist.')
            value = self._decode(uid, old[0])
            for key, item in changes.items():
                if key == 'depends' and isinstance(item, str):
                    item = item.split(',') if item else None
                if item is None or item == '':
                    value.pop(key, None)
                else:
                    value[key] = item
            value = self.validate(value)
            con.execute('UPDATE tasks SET data=? WHERE uuid=?', (json.dumps(value, ensure_ascii=False), uid))
