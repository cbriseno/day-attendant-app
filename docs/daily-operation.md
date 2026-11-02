# Daily operation

## First run and lifecycle

Initialize once with `day-attendant init --zone IANA_ZONE --name NAME`. Restarting
never reseeds a personal profile or changes its timezone. Select another state with
`--state`; the CLI, API and UI share the same coordinator. Do not edit either managed SQLite store directly. Linux and macOS use the same
Python/SQLite task backend.

`service start`, `stop`, `restart`, `status` and `open` operate only the selected
profile. Start is idempotent and the kernel lifetime lock permits one server/profile.
Open starts if needed and obtains a private authenticated loopback URL. Session
credentials persist for reopening; keep the URL private and use `service open` again. Supervised logs contain the
origin, never the authentication fragment. A missing harness leaves every typed change
working; only the conversation, the model's follow-up suggestions and order suggestions
wait for it. Known-data notes still appear on the affected cards.

Run `scheduler install` after reviewing Settings. Linux chooses a usable systemd user
manager, otherwise cron. macOS installs a user LaunchAgent. Jobs execute `tick`, which
never calls a model, reevaluates current facts, attempts permitted reminders and makes
a daily backup. Opening the UI is independent and on demand. `scheduler status` shows
the app's installation receipt; `doctor` shows the last actual tick and transport
failures. A receipt does not prove execution: confirm `last_tick` after installation.
`status` does not claim to validate physical suspend or OS notification permissions.

`service stop` stops the web assistant; reminders continue until disabled in Settings
or removed with `scheduler uninstall`. Uninstall is idempotent and removes only this
profile's identified native job. It preserves tasks, backups and unrelated jobs.
No scheduling adapter promises a popup while the machine is physically suspended.
The next runnable tick reevaluates current conditions instead of replaying missed ticks.

## Editing and local dates

Task fields are edited in their row and save against the latest state read. If the
same field changed elsewhere since you started typing, nothing is sent: the row shows
the current value and keeps your draft, with Save mine and Use the current one. Dialog
editors (capture, calendar, settings, context) use their opening revision; a stale
submission is rejected and the dialog stays open.

Unchanged task deadlines, calendar bounds, reminder pauses and availability times
retain their exact stored instants, including seconds and the resolved occurrence
of a repeated hour. Editing other fields or the profile timezone does not
reinterpret them. Changed local dates use the profile timezone with the service's rules, not the
browser's own time zone data; years outside the usual window are requested from the
service, and a date it cannot confirm is not saved. The browser rejects
missing or repeated local times and retains the draft for correction. Date fields also
show a readable preview in the interface language beside the browser's native picker.

## Agent contract

```sh
day-attendant --json board list
day-attendant --json board request dependency_update \
  --payload '{"uuid":"DEPENDENT_UUID","dependsOn":["PREREQUISITE_UUID"]}' \
  --key human-link-001 --expect 12
day-attendant --json board request related_update \
  --payload '{"uuid":"FIRST_UUID","relatedTo":["SECOND_UUID"]}' --key human-related-001
day-attendant --json board chat 'Capture these selected responsibilities' \
  --image /absolute/selected-notes.png --capture-only --key capture-001
day-attendant --json board request task_update \
  --payload '{"uuid":"TASK_UUID","group":"Office move"}' --key human-group-001 --expect 12
day-attendant --json board request order_update \
  --payload '{"order":["FIRST_UUID","SECOND_UUID"]}' --key human-order-001 --expect 13
day-attendant --json board request group_color_update \
  --payload '{"group":"Office move","color":"teal"}' --key human-color-001 --expect 14
day-attendant --json board suggest --key human-suggest-001
```

Dependency and related updates replace that entity's corresponding list. Preserve
links the human did not ask to remove. Related links are symmetric and nonblocking.
Use permanent UUIDs for writes. The permanent `number` is a display alias, not a positional ID; `board find NUMBER` resolves it to its UUID and current revision. New items in a capture receive UUIDs
independently; requested links between new items need a follow-up using assigned IDs.

`groups` is an ordered list of up to 100 short labels (project, initiative or category), each up to 120 characters, on `task_add` and `task_update`. Replacement lists must preserve memberships the user did not ask to remove. Duplicate keys collapse, using Unicode NFC, lowercase and variation-selector normalization. Emoji remains part of the name. The legacy `group` field still replaces the full list with one group; an empty string clears it. Reads expose authoritative `groups` and a derived first `group` for compatibility. `order_update` replaces the human's display
order (`taskOrder` in `board list`) and is saved without a model review. Use it only when
the human arranges their list; it never changes priority, group or state, and tasks
missing from it follow by priority. `board suggest` asks the selected model once for a
suggested order (`orderSuggestion`); `stale` means tasks or context changed since.
`group_color_update` sets the color a group shows with (`groupColors` in `board list`, keyed
by the lowercase label): `purple`, `teal`, `brown`, `sky`, `pink`, `red`, `orange`, `indigo`,
`green` or `gray`, or `null` for the automatic color its label gives. Like the order it is
the human's presentation, saved without review and with Undo; it changes no task.
Requesting it again with the same key reuses the stored result.

In the UI, **All** counts each open task once. A short row shows the most-used open
groups (three on desktop, two on a phone), with **More** and search for the rest. In group
order a task appears in each membership. Completing any copy completes that same UUID.
A drop replaces only the group it came from; dropping onto a group already assigned removes
the source membership, and dropping into No group removes that source membership. The
other groups remain. Card stripes use the section color there, otherwise their first group.

`group_rename {"group":"Casa","to":"Hogar"}` renames every matching membership,
including completed and retired work. Existing destination spelling and color win a merge;
case-only renames use the requested spelling. One Undo restores the exact original members
and colors, and refuses before any write if a member or affected color state changed. Old
conversation text is preserved. The browser updates its active filter and folded keys too.

Capture shows two most-used groups (including closed cards) plus two most recently assigned,
without repetition. Older groups without assignment history use their real task creation
instants for ranking. The full ranked list opens with **#**, supports arrows/Enter/Tab/Escape,
and preserves group names with spaces as quoted hashtags (`#"Office move"`). New groups
are created directly; a similar-name notice offers the existing spelling without blocking.
The full capture form provides the same multiple-membership selection.

Mode (Light/Dark/Auto) and palette (Graphite/Paper/Ocean) are separate browser preferences.
Explicit mode applies before first paint and takes precedence over system mode; Auto follows
system changes. Native controls use the same resolved CSS color scheme.

The sticky top bar always offers Undo, including Focus. Saved actions announce in a hidden
live region; only errors use a persistent visual banner. The latest 100 eligible original
facts remain undoable after reload, newest first; Undo itself consumes its fact and does not
become a new stack entry. A conflicting top entry reports an error without overwriting data.

Closed responsibilities show the latest ten, grouped by the closing day in the profile's
timezone. Show 10 more reveals the next page; nothing is removed. Reopen and Undo preserve
the recorded closing instant. Older records without a closing date say so instead of
using their creation date. The conversation formats emphasis, lists, code and web/mail
links; supplied HTML remains text.

`board request` applies a valid change in the same call (phase `applied`) or rejects it
with a stable code (`dependency_cycle`, `invalid_uuid`, `task_not_found`,
`stale_revision`…); no model reviews it first. `board list` returns current proposal
phases and individual outcomes. A batch is not one all-or-nothing business transaction:
its interpretations are validated/persisted together, then each item applies in order
against the state the previous one left. Some may save while others no longer apply
(phase `invalid` with its code). Retrying transport keeps the same request identity and
does not create a new batch. An incomplete message with durable proposals reuses them.

Only a retire interpreted from the conversation waits (phase `review`). Use
`board confirm ID --generation N` only after the human confirms that retire;
`--without-review` is accepted for compatibility and changes nothing. Use
`board retry ID` to apply a change an earlier version left waiting, or to ask again
about a stale retire, and `board cancel ID` to discard it.

`board undo FACT_ID --key KEY` restores exactly what a fact replaced and refuses with
`undo_conflict` when a later change touched the same data. It covers task changes,
captures (the new task is retired, never erased), order, available time and rest,
effort and continuity, related links, and calendar additions, edits and cancellations
(the same commitment returns with its UUID); it does not cover provenance or recorded
progress. `board undo-message
MESSAGE_KEY --key KEY` undoes every change one conversation message applied, newest
first.

After a pause of a few seconds the service looks at new facts and records suggestions,
listed under `suggestions` in `board list` (`current` while their facts still hold) with
the review state under `review`. `board accept ID` applies a suggested change as a typed
request, with Undo; `board dismiss ID` hides it for good. Neither the review nor a
suggestion ever changes a task by itself.

## Settings and notification policy

```sh
day-attendant --json profile show
day-attendant --json profile configure --key select-claude-001 \
  --values '{"harness":"claude","model":null,"effort":"high"}'
day-attendant --json board clear --key new-conversation-001
day-attendant --json profile configure --key backup-location-001 \
  --values '{"backup_directory":"/absolute/approved/backup-directory"}'
```

`effort` selects the reasoning level the harness offers for the model; an unavailable
level is rejected instead of replaced. Changing `harness` without `effort` resets the level
to unset, as it resets `model`. `board clear` (or a chat message that is exactly
`/clear`) starts a new conversation and is idempotent per key. It is refused while a
reply or contextual guidance is pending. Earlier messages remain in the profile and its backups.

Exact model IDs are pinned after resolution. A model alias that resolves to another
identifier is rejected; use the resolved exact ID. No automatic change of harness,
provider or billing method occurs after authentication, quota or model errors.
Use the UI Settings for working days, delivery/quiet times, pause, repeat period and
budgets. `notification_policy` is also a typed JSON object in `profile configure`.
The initial Mon–Fri 09:00–18:00 default is not an assertion about your working hours.
Equal quiet start/end disables that quiet window; delivery start/end must differ.

Delivery failures consume the configured attempt budgets; silence consumes none.
Uncertain outcomes require inspection rather than automatic resend. A notifier
accepting an alert never proves that a person read it. Unchanged repeats are slow,
and never-notified work is favored before repeats to avoid starvation. A rolling
three-attempt/five-minute ceiling also covers concurrent callers and clock changes.

## Backups, maintenance and recovery

Use `backup create [--destination DIR] [--key KEY]`, `backup list`, and `backup verify
ARCHIVE`. The default private backup directory is outside the profile and checkout.
The scheduler retains seven daily and four weekly snapshots; manual and migration
copies are not pruned by that policy. Keep a verified independent copy for disk loss.
No cloud transfer or cross-device synchronization is enabled.

Snapshot maintenance prevents new admissions, image writes and delivery claims,
invalidates in-flight reasoning, waits boundedly for transport and captures both
SQLite stores with their backup APIs. Already observed partial operations are
preserved for diagnosis; a backup does not execute an operation on your behalf.
Compression happens from immutable staged files and publication is atomic. A failed
backup preserves existing archives/profile and surfaces a diagnostic error.

`restore ARCHIVE --to NEW_DIRECTORY` is offline and never overwrites an occupied
profile. It verifies allowed members, hashes, database integrity, native UUIDs,
dependency graphs, relation references and authorization for incomplete operations.
It creates a distinct profile identity, discards runtime credentials/jobs, invalidates
reasoning and disables reminders. Historical current candidates also have a 24-hour
hold to reduce replay. Review Settings before reenabling. This is not exactly-once
external notification delivery or live multi-machine synchronization.

Conflicts open a read-only UI with **Diagnostics → Review recovery**. Compare expected,
intended and observed native state. Completing is permitted only if every participant
matches its recorded before/after state and the auxiliary revision matches. Keeping
observed data abandons the interrupted operation without undoing partial/external
changes or claiming completion. Both routes take a backup, compare preconditions
again and record the decision. CLI equivalent:

```sh
day-attendant --json reconcile 'proposal:OPERATION_UUID'
day-attendant --json reconcile 'proposal:OPERATION_UUID' \
  --resolution keep_observed --precondition OBSERVED_DIGEST
```

Never use manual SQLite edits, blanket force or deletion of private state as recovery.
If maintenance was interrupted, retry a backup: a dead maintenance owner is reconciled
under the writer lock. An active owner remains protected; check `doctor` before retry.

## Task storage upgrade and rollback

With the selected service stopped, `profile upgrade` takes a verified coherent backup,
checks its task fingerprint and revision again under the coordinator lock, and upgrades
the task store in one SQLite transaction. Schema 3 converts a nonempty single `project`
into an ordered list and registers all tasks, including closed/retired/recurring records,
in an append-only numeric alias table. Migration order is creation instant then UUID.
Aliases are never removed or reused; retries preserve existing mappings. No last-active
instant is invented for a task without a real `start`/recorded activity. The existing
`priority_migration` receipt now records task schema 3 and the verified source backup.

A failed backup leaves schema and task bytes intact. An incomplete operation must first be
recovered or reconciled against its original schema; no migration bypasses that journal.
Startup fails closed on an upgrade error. Offline restore verifies old archives before
upgrading their copy, using that exact verified archive as the migration backup. Restored
incomplete operations stay on their original schema for supervised reconciliation first.
No old backup directory is written merely by testing/restoring an archive.

Before activation retain the verified migration archive and record the selected profile,
revision, UUID/count digest, task-order/colors/preferences, current process and code head.
After upgrade compare the same facts, plus alias uniqueness and `/theme.js`/UI asset health.
Rollback uses a verified pre-upgrade archive restored into a **new** directory with the
matching earlier release; never change `user_version`, overwrite the live profile or use an
old executable on a schema-3 store. `restore` disables reminders and changes profile identity;
review those settings before selecting a restored profile. The supervisor owns local landing
and production restart.
