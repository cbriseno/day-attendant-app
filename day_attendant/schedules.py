"""Per-task repetition and reminders (#41). Pure functions; storage lives in profile state."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from .errors import AssistantError
from .timeutil import instant, parse, stamp

EVERY = ('day', 'weekday', 'week', 'month', 'days')
REMINDER_KINDS = ('before', 'day_before', 'at')
MAX_REMINDERS = 10
# A reminder that fired more than this long ago is history, not a notice.
REMINDER_WINDOW = timedelta(hours=12)


def validate(value):
    """Normalize {repeat, reminders}; None or empty clears the schedule."""
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) - {'repeat', 'reminders'}:
        raise AssistantError('invalid_schedule', 'Use repeat and reminders only.')
    repeat = value.get('repeat')
    if repeat is not None:
        if not isinstance(repeat, dict) or repeat.get('every') not in EVERY or set(repeat) - {'every', 'days', 'n'}:
            raise AssistantError('invalid_schedule', 'Choose daily, weekdays, weekly, monthly or every N days.')
        clean = {'every': repeat['every']}
        if repeat['every'] == 'week':
            days = repeat.get('days') or []
            if not isinstance(days, list) or not days or any(type(d) is not int or d not in range(7) for d in days):
                raise AssistantError('invalid_schedule', 'A weekly repetition needs weekdays from Monday 0 to Sunday 6.')
            clean['days'] = sorted(set(days))
        if repeat['every'] == 'days':
            n = repeat.get('n')
            if type(n) is not int or not 1 <= n <= 365:
                raise AssistantError('invalid_schedule', 'Repeat every 1 to 365 days.')
            clean['n'] = n
        repeat = clean
    reminders = value.get('reminders') or []
    if not isinstance(reminders, list) or len(reminders) > MAX_REMINDERS:
        raise AssistantError('invalid_schedule', 'Use up to 10 reminders.')
    out = []
    for item in reminders:
        if not isinstance(item, dict) or item.get('kind') not in REMINDER_KINDS:
            raise AssistantError('invalid_schedule', 'Unknown reminder.')
        if item['kind'] == 'before':
            m = item.get('minutes')
            if type(m) is not int or not 1 <= m <= 60 * 24 * 30:
                raise AssistantError('invalid_schedule', 'Reminder minutes must be positive.')
            out.append({'kind': 'before', 'minutes': m})
        elif item['kind'] == 'day_before':
            t = item.get('time')
            try:
                if not isinstance(t, str) or datetime.strptime(t, '%H:%M').strftime('%H:%M') != t:
                    raise ValueError()
            except ValueError as error:
                raise AssistantError('invalid_schedule', 'Use HH:MM for the day-before reminder.') from error
            out.append({'kind': 'day_before', 'time': t})
        else:
            at = item.get('at')
            if not isinstance(at, str):
                raise AssistantError('invalid_schedule', 'A custom reminder needs a date and time.')
            out.append({'kind': 'at', 'at': stamp(parse(at))})
    unique = []
    for item in out:
        if item not in unique:
            unique.append(item)
    if repeat is None and not unique:
        return None
    return {'repeat': repeat, 'reminders': unique}


def next_due(due, repeat, zone, now):
    """The next local occurrence after both the current due date and now, keeping wall time."""
    tz = ZoneInfo(zone or 'UTC')
    local = parse(due).astimezone(tz) if due else now.astimezone(tz).replace(hour=9, minute=0, second=0, microsecond=0)
    current = local
    for _ in range(800):
        every = repeat['every']
        if every == 'day':
            current = current + timedelta(days=1)
        elif every == 'days':
            current = current + timedelta(days=repeat['n'])
        elif every == 'weekday':
            current = current + timedelta(days=1)
            while current.weekday() > 4:
                current = current + timedelta(days=1)
        elif every == 'week':
            current = current + timedelta(days=1)
            while current.weekday() not in repeat['days']:
                current = current + timedelta(days=1)
        else:  # month: same day, clamped to the month's end
            year, month = (current.year + (current.month == 12), current.month % 12 + 1)
            day = local.day
            while True:
                try:
                    current = current.replace(year=year, month=month, day=day)
                    break
                except ValueError:
                    day -= 1
        # Rebuild from wall-clock fields so a DST change keeps 09:00 at 09:00.
        current = datetime(current.year, current.month, current.day, local.hour, local.minute, tzinfo=tz)
        if current > now.astimezone(tz):
            return instant(current.replace(tzinfo=None).isoformat(), zone or 'UTC')
    raise AssistantError('invalid_schedule', 'No next occurrence found.')


def reminder_instants(schedule, due, zone):
    """Each reminder resolved to an instant; reminders tied to a due date need one."""
    tz = ZoneInfo(zone or 'UTC')
    result = []
    for item in (schedule or {}).get('reminders') or []:
        if item['kind'] == 'at':
            result.append((item, item['at']))
        elif not due:
            continue
        elif item['kind'] == 'before':
            result.append((item, stamp(parse(due) - timedelta(minutes=item['minutes']))))
        else:
            hour, minute = map(int, item['time'].split(':'))
            day = parse(due).astimezone(tz) - timedelta(days=1)
            result.append((item, stamp(datetime(day.year, day.month, day.day, hour, minute, tzinfo=tz))))
    return result


def notice_text(kind, title, locale='en'):
    es = locale == 'es'
    prefix = {
        'due': 'Por vencer' if es else 'Due soon',
        'overdue': 'Venció' if es else 'Overdue',
        'reminder': 'Recordatorio' if es else 'Reminder',
        'event': 'Agenda' if es else 'Agenda',
        'snooze_ready': 'Vuelve hoy' if es else 'Back today',
        'stale': 'Sin movimiento' if es else 'No movement',
        'chat_waiting': 'Pendiente de la conversación' if es else 'Waiting from chat',
    }.get(kind)
    return prefix + ' · ' + title if prefix else title
