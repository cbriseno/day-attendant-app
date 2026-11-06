# Conversation and app operations

Chat receives current tasks (including closed work), events, assigned group labels,
saved schedules, notification policy, profile, presentation, proposal/suggestion IDs,
Undo facts and check-ins on every turn. It uses a fresh native session with the same
contract for Codex and Claude. This is selected app state, not arbitrary access to
source code, files, credentials, external sources or HTTP URLs.

## Usage guidance and support reports

Every chat turn also receives `appHelp`: the current README, this contract and
the operation guide, plus UI view/control definitions, keyboard-handler excerpts,
ordering rules and referenced English/Spanish captions read from the shipped
sources. There is no separately maintained feature catalog. Source installations
must keep these docs beside the Python package, as described in the README.
Action and route schemas remain the authority for executable operations.
The public UI excerpts do not expose the current browser view or preferences.

The assistant guides use step by step and distinguishes an existing function,
a probable bug (reported behavior differs from documented behavior), a feature
gap, and insufficient evidence. It explains unavailable execution separately from
missing product support. A probable bug is not a verified diagnosis.
Help and report requests alone make no state changes.

On request it drafts a Markdown report with a title, classification, context,
steps or desired workflow, actual/expected results and unknowns. Missing facts
are marked as not supplied. The existing **Download record** action lets the user
edit and download only that reply locally. Reports are never submitted externally;
unrelated tasks, history, profile data and diagnostics are excluded. Drafting adds
no confirmation step and gives the model no file or browser access.

`action_contract.py` defines the coordinator's public action/field boundary and
field schemas; `Connected.request` and conversation use that same definition.
`api_contract.py` defines fixed app routes and argument types; the HTTP handlers and
conversation use those route definitions. The context includes their descriptions
and types. Changes still use the existing validators, receipts, retirement
confirmation and Undo. No additional confirmation layer or schedule engine exists.

Null model fields mean omitted. Explicit removal uses `clearFields` (the existing
API's empty string/list/null as appropriate), `clearDue`, `clearRepeat` or
`clearSchedule`. Classification adds a clearly relevant existing label only when
the human asks to classify; it preserves existing memberships. New chat labels must
be human-named. Groups have no independent catalog: create one by assigning a label,
rename/merge it with `group_rename`, remove it from the requested tasks via their
groups lists. Ambiguous classification remains a question.

## Coordinator operations

| Action | Fields | Function |
| --- | --- | --- |
| `task_add` | `attachmentIds`, `awaiting`, `captureText`, `context`, `due`, `estimate_minutes`, `group`, `groups`, `next`, `observed_at`, `organize`, `person`, `priority`, `reference`, `remainingMinutes`, `source`, `title`, `zone` | Create a responsibility with priority, due date, groups, provenance and continuity. |
| `task_update` | `assistantNotes`, `awaiting`, `context`, `due`, `group`, `groups`, `next`, `nextUp`, `order`, `original`, `priority`, `progress`, `remainingMinutes`, `title`, `taskId`, `zone` | Edit a task; empty groups removes all memberships, nextUp selects the next task. |
| `front_activate` | `order`, `taskId` | Start a task now. |
| `front_todo` | `order`, `taskId` | Return a task to todo. |
| `front_retire` | `taskId` | Retire/delete a task without completing it; existing chat confirmation applies. |
| `task_snooze` | `fold`, `order`, `until`, `taskId`, `zone` | Snooze until a local or offset date. |
| `task_done` | `taskId` | Complete an occurrence; repeating tasks advance their due date. |
| `task_reopen` | `taskId` | Reopen completed or retired work. |
| `task_cancel` | `reason`, `taskId` | Cancel a responsibility without completing it; retain its checklist. |
| `context_update` | `availableMinutes`, `availableUntil`, `rest` | Declare available time or rest. |
| `continuity_update` | `assistantNotes`, `awaiting`, `blockReason`, `checklist`, `context`, `next`, `notes`, `original`, `remainingMinutes`, `taskId` | Edit remaining effort, waiting, context, next step, notes, checklist, or manual outside block (empty blockReason removes it). |
| `dependency_update` | `dependsOn`, `taskId` | Replace blocking prerequisite UUIDs; preserve unrequested links. |
| `related_update` | `relatedTo`, `taskId` | Replace symmetric nonblocking related UUIDs; preserve unrequested links. |
| `schedule_update` | `reminders`, `repeat`, `taskId` | Configure repetition and multiple alerts; chat preserves omitted fields and requires explicit cancellation. |
| `attachments_update` | `attachmentIds`, `taskId` | Replace task links to existing selected attachment UUIDs. |
| `organize_capture` | `expectedTitle`, `original`, `tasks`, `taskId` | Organize an unchanged saved capture into tasks with notes, categories and zero-based prerequisite indices. |
| `order_update` | `order` | Set manual display order, preserving other tasks; does not change priority. |
| `group_rename` | `group`, `to` | Rename or merge all matching memberships, including closed tasks. Groups exist only as assigned labels. |
| `group_color_update` | `color`, `group` | Set a group palette color; clearFields=[color] restores automatic color. |
| `provenance_update` | `observed_at`, `person`, `reference`, `source`, `taskId`, `zone` | Edit the human-supported source, person, reference and observed time. |
| `event_add` | `end`, `fold`, `observed_at`, `person`, `reference`, `source`, `start`, `title`, `zone` | Create a calendar commitment. |
| `event_update` | `end`, `fold`, `start`, `title`, `taskId`, `zone` | Edit a calendar commitment. |
| `event_cancel` | `taskId` | Cancel a calendar commitment. |

## Other app endpoints

Named app operations use `operationPayload`. Only the service supplies its own
origin, token, request keys and revisions. The model cannot choose a destination or
credentials. In direct, unserved Conversation fixtures, `localApiAvailable=false`
reports that app endpoints cannot execute. Optional nullable arguments are omitted;
profile notification patches preserve saved policy fields, including kind switches.
`clearSettings` explicitly resets model/effort to null. API results are appended to
the existing reply, including failures; they are never inferred from the model's
text. Interpretation finishes before maintenance or semantic settings changes so
those existing operations do not invalidate their own reply. Task proposals apply
first if a reply also requests app operations.

| Operation | Endpoint | Function |
| --- | --- | --- |
| `profile_configure` | `POST /api/settings` | Change profile, language, timezone, assistant selection, notification policy, organizer or backup directory. |
| `assistant_mode` | `POST /api/agent-mode` | Pause, turn off or resume assistant use. When off, resume through the UI. |
| `checkins_settings` | `POST /api/proactive` | Configure the existing optional check-ins. |
| `checkins_run` | `POST /api/proactive` | Run the existing check-in pass once; uses the selected model. |
| `checkins_answer` | `POST /api/proactive` | Answer an offered check-in using its offered answer. |
| `proposal_confirm` | `POST /api/proposals/{id}/confirm` | Confirm an existing retirement proposal at its current generation. |
| `proposal_cancel` | `POST /api/proposals/{id}/cancel` | Cancel a pending proposal. |
| `proposal_retry` | `POST /api/proposals/{id}/retry` | Retry an existing proposal without recreating it. |
| `undo_fact` | `POST /api/undo` | Undo an existing fact using the existing conflict checks. |
| `undo_message` | `POST /api/undo` | Undo the proposals from a selected conversation message. |
| `undo_proposals` | `POST /api/undo` | Undo selected applied proposals. |
| `undo_organization` | `POST /api/organization/undo` | Undo organized capture; partial=true keeps conflicting later edits. |
| `suggestion_accept` | `POST /api/suggestions/{id}/accept` | Accept an existing current suggestion. |
| `suggestion_dismiss` | `POST /api/suggestions/{id}/dismiss` | Dismiss an existing suggestion. |
| `order_suggest` | `POST /api/suggestion` | Request an advisory ordering using the selected model; never changes manual order. |
| `backup_create` | `POST /api/backups` | Create a local backup using configured storage. |
| `backup_list` | `GET /api/backups` | List local backups. |
| `recovery_inspect` | `POST /api/recovery/inspect` | Inspect an incomplete operation before a supervised recovery choice. |
| `recovery_resolve` | `POST /api/recovery/resolve` | Apply the explicit recovery choice using its observed precondition. |
| `doctor` | `GET /api/doctor` | Inspect local diagnostics; does not repair anything. |
| `model_list` | `GET /api/models` | List available harness model catalogs; does not change selection. |
| `zone_rules` | `GET /api/zone-rules` | Inspect profile timezone rules for a year. |
| `diagnostics_preview` | `GET /api/diagnostics/preview` | Preview diagnostic export contents. |
| `diagnostics_export` | `POST /api/diagnostics/export` | Use the existing diagnostic export, not a conversation document. |
| `attachment_read` | `GET /api/attachments/{id}` | Read a selected attachment; binary content remains in the attachment UI. |
| `attachment_upload` | `POST /api/attachments` | Save explicitly supplied attachment bytes, never invented file contents. |
| `chat_retry` | `POST /api/chat/retry` | Retry an earlier incomplete message using its original key. |
| `service_shutdown` | `POST /api/shutdown` | Stop this local app service only on an explicit request. |

The remaining API routes are existing conversation/transport infrastructure:

- `POST /api/session` exchanges the UI credential; it is never exposed to the model.
- `GET /api/state` supplies the selected current context above.
- `POST /api/proposals` carries coordinator actions in the first table.
- `POST /api/chat` submits the human turn; chat cannot recursively submit new turns.
- `POST /api/chat/clear` is already available through the literal human `/clear`
  command, which starts a fresh conversation after pending work finishes.
- `POST /api/proactive` with `tick` is the page's existing cadence mechanism;
  `checkins_run` exposes the explicit manual pass. No new unattended loop exists.

The browser's theme, palette and anonymization preferences are local UI choices,
not coordinator data. Offline restore, migration and native scheduler installation
are host procedures, not connected HTTP operations. Attachment upload can carry
explicitly supplied bytes; the model cannot read a local path to obtain them.
Conversation document export is a separate feature; diagnostics export is the
existing diagnostic operation and does not export selected conversation prose.

## Scheduling limits

For a saved UUID, weekday repetition and multiple alerts can be set, queried and
edited. Omitted repeat/reminder fields preserve saved settings; a supplied reminder
list retains alerts not requested for removal. A new capture needs its permanent
UUID before a follow-up schedule action. Repetition advances due dates when an
occurrence is completed. Weekday means Monday-Friday without holiday data; there
is no external milestone stop condition or autonomous external status check.
Delivery policy and scheduler status do not establish delivery or that a person
read a notification. Turning assistant use off prevents further interpretation;
resume through its existing UI control.
