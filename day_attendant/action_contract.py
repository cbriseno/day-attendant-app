"""Shared coordinator action names, field types and human-facing semantics."""
from .taskstore import PRIORITIES
from .schedules import EVERY, MAX_REMINDERS
from .service import GROUP_COLORS, CHECKLIST_LIMIT

ALLOWED = {
    "task_add": {"title", "priority", "due", "source", "zone", "person", "reference", "observed_at", "estimate_minutes", "remainingMinutes", "awaiting", "context", "next", "group", "groups", "attachmentIds", "organize", "captureText"},
    "task_update": {"uuid", "title", "nextUp", "priority", "due", "zone", "progress", "context", "next", "awaiting", "remainingMinutes", "original", "assistantNotes", "group", "groups", "order"},
    "front_activate": {"uuid", "order"}, "front_todo": {"uuid", "order"}, "front_retire": {"uuid"},
    "task_snooze": {"uuid", "until", "zone", "fold", "order"}, "task_done": {"uuid"}, "task_reopen":{"uuid"}, "task_cancel":{"uuid","reason"},
    "context_update": {"availableMinutes", "availableUntil", "rest"},
    "continuity_update": {"uuid", "remainingMinutes", "awaiting", "context", "next", "notes", "original", "assistantNotes", "checklist", "blockReason"},
    "dependency_update": {"uuid","dependsOn"},
    "related_update": {"uuid","relatedTo"},
    "schedule_update": {"uuid","repeat","reminders"},
    "attachments_update": {"uuid","attachmentIds"},
    "organize_capture": {"uuid","original","expectedTitle","tasks"},
    "order_update": {"order"},
    "group_rename": {"group", "to"},
    "group_color_update": {"group", "color"},
    "provenance_update": {"uuid","source","person","reference","observed_at","zone"},
    "event_add": {"title","start","end","zone","fold","source","person","reference","observed_at"},
    "event_update": {"uuid","title","start","end","zone","fold"},
    "event_cancel": {"uuid"},
}

SCHEMAS={
    **{key:{"type":["string","null"]} for key in ('uuid','title','due','until','context','next','source','person','reference','observed_at','start','end','group')},
    'priority':{'type':['string','null'],'enum':[*PRIORITIES,None]},
    **{key:{'type':['number','null']} for key in ('remainingMinutes','availableMinutes','estimate_minutes')},
    **{key:{'type':['boolean','null']} for key in ('awaiting','rest','progress')},
    'availableUntil':{'type':['string','null']},
    'dependsOn':{'type':['array','null'],'items':{'type':'string'}},
    'groups':{'type':['array','null'],'items':{'type':'string'}},
    'relatedTo':{'type':['array','null'],'items':{'type':'string'}},
    'repeat':{'anyOf':[{'type':'null'},{'type':'object','properties':{
        'every':{'type':'string','enum':list(EVERY)},'days':{'type':['array','null'],'items':{'type':'integer','minimum':0,'maximum':6}},
        'n':{'type':['integer','null'],'minimum':1,'maximum':365}},'required':['every','days','n'],'additionalProperties':False}]},
    'reminders':{'type':['array','null'],'maxItems':MAX_REMINDERS,'items':{'anyOf':[
        {'type':'object','properties':{'kind':{'type':'string','enum':['before']},'minutes':{'type':'integer','minimum':1,'maximum':43200}},'required':['kind','minutes'],'additionalProperties':False},
        {'type':'object','properties':{'kind':{'type':'string','enum':['day_before']},'time':{'type':'string'}},'required':['kind','time'],'additionalProperties':False},
        {'type':'object','properties':{'kind':{'type':'string','enum':['at']},'at':{'type':'string'}},'required':['kind','at'],'additionalProperties':False}]}},
}

CONTROLS={'taskId':{'type':['string','null']},'clearDue':{'type':'boolean'},
    'classifyGroups':{'type':['boolean','null']},'clearSchedule':{'type':['boolean','null']},
    'clearRepeat':{'type':['boolean','null']},'clearFields':{'type':['array','null'],'items':{'type':'string'}},
    'userAuthorized':{'type':'boolean'},'requestEvidence':{'type':'string'}}

SCHEMAS.update({
    **{key:{'type':['string','null']} for key in ('zone','to','reason','notes','original','assistantNotes','blockReason','captureText','expectedTitle')},
    **{key:{'type':['boolean','null']} for key in ('nextUp','organize')},
    **{key:{'type':['array','null'],'items':{'type':'string'}} for key in ('attachmentIds','order')},
    'fold':{'type':['integer','null'],'enum':[0,1,None]},
    'color':{'type':['string','null'],'enum':[*GROUP_COLORS,None]},
    'checklist':{'type':['array','null'],'maxItems':CHECKLIST_LIMIT,'items':{'type':'object','properties':{
        'id':{'type':'string'},'text':{'type':'string'},'done':{'type':'boolean'}},'required':['id','text','done'],'additionalProperties':False}},
    'tasks':{'type':['array','null'],'items':{'type':'object','properties':{
        'title':{'type':'string'},'notes':{'type':'string'},'groups':{'type':'array','items':{'type':'string'}},
        'after':{'type':'array','items':{'type':'integer'}}},'required':['title','notes','groups','after'],'additionalProperties':False}}})

DESCRIPTIONS={
    'task_add':'Create a responsibility with priority, due date, groups, provenance and continuity.',
    'task_update':'Edit a task; empty groups removes all memberships, nextUp selects the next task.',
    'front_activate':'Start a task now.', 'front_todo':'Return a task to todo.',
    'front_retire':'Retire/delete a task without completing it; existing chat confirmation applies.',
    'task_snooze':'Snooze until a local or offset date.', 'task_done':'Complete an occurrence; repeating tasks advance their due date.',
    'task_reopen':'Reopen completed or retired work.', 'task_cancel':'Cancel a responsibility without completing it; retain its checklist.',
    'context_update':'Declare available time or rest.',
    'continuity_update':'Edit remaining effort, waiting, context, next step, notes, checklist, or manual outside block (empty blockReason removes it).',
    'dependency_update':'Replace blocking prerequisite UUIDs; preserve unrequested links.',
    'related_update':'Replace symmetric nonblocking related UUIDs; preserve unrequested links.',
    'schedule_update':'Configure repetition and multiple alerts; chat preserves omitted fields and requires explicit cancellation.',
    'attachments_update':'Replace task links to existing selected attachment UUIDs.',
    'organize_capture':'Organize an unchanged saved capture into tasks with notes, categories and zero-based prerequisite indices.',
    'order_update':'Set manual display order, preserving other tasks; does not change priority.',
    'group_rename':'Rename or merge all matching memberships, including closed tasks. Groups exist only as assigned labels.',
    'group_color_update':'Set a group palette color; clearFields=[color] restores automatic color.',
    'provenance_update':'Edit the human-supported source, person, reference and observed time.',
    'event_add':'Create a calendar commitment.', 'event_update':'Edit a calendar commitment.', 'event_cancel':'Cancel a calendar commitment.'}

ACTIONS=list(ALLOWED)
FIELDS={'action':{'type':'string','enum':ACTIONS},**{key:SCHEMAS[key] for key in sorted(set().union(*ALLOWED.values())-{'uuid'})},**CONTROLS}


def action_contract():
    return {action:{'description':DESCRIPTIONS[action],
            'fields':{('taskId' if field=='uuid' else field):SCHEMAS[field] for field in sorted(names)}}
            for action,names in ALLOWED.items()}

# Existing API removal values; absent nullable model fields still mean no change.
CLEAR_VALUES={**{k:'' for k in ('context','next','notes','original','assistantNotes','blockReason')},
    **{k:[] for k in ('groups','dependsOn','relatedTo','attachmentIds','checklist','order')}}
