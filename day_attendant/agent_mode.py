"""Persistent control over model use; local reminders and backups are unaffected."""
from datetime import timedelta
from zoneinfo import ZoneInfo

from .errors import AssistantError
from .service import encoded
from .timeutil import parse, stamp


def current(store, now):
    value = store.state_value('agent_mode', {'mode': 'active', 'until': None})
    if value['mode'] == 'paused' and value.get('until') and parse(value['until']) <= now:
        return {'mode': 'active', 'until': None}
    return value


def set_mode(app, mode, duration=None):
    if mode not in ('active', 'paused', 'off') or (mode == 'paused' and duration not in ('1h', 'today', 'forever')) or (mode != 'paused' and duration is not None):
        raise AssistantError('invalid_agent_mode', 'Choose active, off, or a pause duration.')
    with app.store.lock():
        app.store.assert_writable()
        now = app.clock()
        end = None
        if mode == 'paused' and duration == '1h':
            end = now + timedelta(hours=1)
        elif mode == 'paused' and duration == 'today':
            local = now.astimezone(ZoneInfo(app.store.state_value('timezone', 'UTC')))
            end = (local + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        value = {'mode': mode, 'until': stamp(end) if end else None}
        if mode == 'paused':
            value['duration'] = duration
        with app.store.connect() as con:
            con.execute("INSERT OR REPLACE INTO state VALUES('agent_mode',?)", (encoded(value),))
        return value


def require_allowed(store, now):
    value = current(store, now)
    if value['mode'] != 'active':
        raise AssistantError('agent_paused' if value['mode'] == 'paused' else 'agent_off',
                             'Assistant use is paused or off. Local reminders and backups still work.')
