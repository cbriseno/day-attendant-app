"""Named access to existing local app endpoints; never arbitrary URLs or credentials."""


from .proactive import KINDS


def obj(properties):
    return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}


TEXT={'type':['string','null']}
BOOL={'type':['boolean','null']}
NUMBER={'type':['integer','null']}
STRINGS={'type':['array','null'],'items':{'type':'string'}}
POLICY=obj({**{k:BOOL for k in ('enabled','technicalDefault')},
    **{k:TEXT for k in ('timezone','start','end','quietStart','quietEnd','pausedUntil')},
    'weekdays':{'type':['array','null'],'items':{'type':'integer'}},
    **{k:NUMBER for k in ('intervalMinutes','unchangedRepeatMinutes','dailyBudget')},
    'kinds':{'anyOf':[{'type':'null'},obj({k:BOOL for k in ('soon','overdue','reminder')})]}})
SETTINGS=obj({**{k:TEXT for k in ('name','timezone','locale','harness','model','effort','backup_directory')},
    'autoOrganize':BOOL,'notification_policy':{'anyOf':[{'type':'null'},POLICY]}})
CHECKINS=obj({'enabled':BOOL,'every':NUMBER,'quietStart':TEXT,'quietEnd':TEXT,'maxPerDay':NUMBER,
    'kinds':{'anyOf':[{'type':'null'},obj({k:BOOL for k in KINDS})]}})

# name: method, fixed route, description, typed arguments. Dynamic routes use only supplied IDs.
OPERATIONS={
 'profile_configure':('POST','/api/settings','Change profile, language, timezone, assistant selection, notification policy, organizer or backup directory.',{'values':SETTINGS,'clearSettings':STRINGS}),
 'assistant_mode':('POST','/api/agent-mode','Pause, turn off or resume assistant use. When off, resume through the UI.',{'mode':TEXT,'duration':TEXT}),
 'checkins_settings':('POST','/api/proactive','Configure the existing optional check-ins.',{'values':CHECKINS}),
 'checkins_run':('POST','/api/proactive','Run the existing check-in pass once; uses the selected model.',{}),
 'checkins_answer':('POST','/api/proactive','Answer an offered check-in using its offered answer.',{'id':TEXT,'answer':TEXT}),
 'proposal_confirm':('POST','/api/proposals/{id}/confirm','Confirm an existing retirement proposal at its current generation.',{'id':TEXT,'generation':NUMBER}),
 'proposal_cancel':('POST','/api/proposals/{id}/cancel','Cancel a pending proposal.',{'id':TEXT}),
 'proposal_retry':('POST','/api/proposals/{id}/retry','Retry an existing proposal without recreating it.',{'id':TEXT}),
 'undo_fact':('POST','/api/undo','Undo an existing fact using the existing conflict checks.',{'fact_id':NUMBER}),
 'undo_message':('POST','/api/undo','Undo the proposals from a selected conversation message.',{'message_key':TEXT}),
 'undo_proposals':('POST','/api/undo','Undo selected applied proposals.',{'proposal_ids':STRINGS}),
 'undo_organization':('POST','/api/organization/undo','Undo organized capture; partial=true keeps conflicting later edits.',{'fact_id':NUMBER,'partial':BOOL}),
 'suggestion_accept':('POST','/api/suggestions/{id}/accept','Accept an existing current suggestion.',{'id':TEXT}),
 'suggestion_dismiss':('POST','/api/suggestions/{id}/dismiss','Dismiss an existing suggestion.',{'id':TEXT}),
 'order_suggest':('POST','/api/suggestion','Request an advisory ordering using the selected model; never changes manual order.',{}),
 'backup_create':('POST','/api/backups','Create a local backup using configured storage.',{}),
 'backup_list':('GET','/api/backups','List local backups.',{}),
 'recovery_inspect':('POST','/api/recovery/inspect','Inspect an incomplete operation before a supervised recovery choice.',{'operation_key':TEXT}),
 'recovery_resolve':('POST','/api/recovery/resolve','Apply the explicit recovery choice using its observed precondition.',{'operation_key':TEXT,'resolution':TEXT,'precondition':TEXT}),
 'doctor':('GET','/api/doctor','Inspect local diagnostics; does not repair anything.',{}),
 'model_list':('GET','/api/models','List available harness model catalogs; does not change selection.',{}),
 'zone_rules':('GET','/api/zone-rules','Inspect profile timezone rules for a year.',{'year':NUMBER}),
 'diagnostics_preview':('GET','/api/diagnostics/preview','Preview diagnostic export contents.',{}),
 'diagnostics_export':('POST','/api/diagnostics/export','Use the existing diagnostic export, not a conversation document.',{}),
 'attachment_read':('GET','/api/attachments/{id}','Read a selected attachment; binary content remains in the attachment UI.',{'id':TEXT}),
 'attachment_upload':('POST','/api/attachments','Save explicitly supplied attachment bytes, never invented file contents.',{'name':TEXT,'mime':TEXT,'base64':TEXT,'purpose':TEXT}),
 'chat_retry':('POST','/api/chat/retry','Retry an earlier incomplete message using its original key.',{'message_key':TEXT}),
 'service_shutdown':('POST','/api/shutdown','Stop this local app service only on an explicit request.',{}),
}


def operation_contract():
    return {name:{'description':description,'fields':fields,'method':method,'route':route}
            for name,(method,route,description,fields) in OPERATIONS.items()}


ROUTES={name:entry[1] for name,entry in OPERATIONS.items()}


OPERATION_SCHEMA={'anyOf':[{'type':'null'},*[obj(fields) for _,_,_,fields in OPERATIONS.values()]]}


def supplied(value):
    """Required nullable schema fields represent omitted API arguments."""
    if isinstance(value,dict):return {k:supplied(v) for k,v in value.items() if v is not None}
    if isinstance(value,list):return [supplied(v) for v in value]
    return value
