# Current daily architecture

A portable Python domain
owns all writes through a shared coordinator and durable journal. The same
standard-library Python/SQLite task store (`tasks.sqlite3`) is the task authority
on Linux and macOS; a companion SQLite database stores calendar events, declarations, provenance,
relations, messages, proposals, authorization, facts and delivery receipts.

Codex app-server and Claude Code CLI implement the same inference interface with a
selected model and reasoning level. Each turn uses a fresh native session; the model
receives profile facts, the current conversation since `/clear` and selected images, has no external task-writing
tools, and returns typed interpretations and follow-up suggestions. The selected
harness/model is validated for every turn. Epochs, generations, fingerprints and native
read/write guards prevent stale application.

A typed change is validated deterministically (schema, UUIDs, `--expect`, cycles,
references) and admitted and applied in its own request, with no model turn first. Each
fact keeps the values it replaced, so Undo restores them and refuses when a later change
touched the same data. After a pause in activity the service looks at the new facts:
known-data rules note consequences (an unblocked dependent, a resume after the deadline
or during a commitment, active work that still waits, a capacity overflow) and the
selected model may add grounded suggestions about the changed responsibilities. That
review runs outside every request and outside the writer lock, writes only suggestions
tied to a task and to the facts they relied on, and never blocks, applies or undoes a
change. Without new facts it spends no model turn. A conversation's interpreted changes
apply the same way; only a retire from the conversation waits for the person.

Pending interpretations are not executable operations. Admission records a decision,
operation and admitted transition together. An incomplete executable operation prevents
admission of another until recovery/reconciliation. Native recovery compares its
write participants against before/after states and its read set against recorded
preconditions; it does not overwrite changed prerequisites or external native edits.

Blocking graph edges are task-record dependency UUIDs; related pairs are sorted
symmetric SQLite links. Active, snoozed, awaiting and blocked are independent facts.

Kernel locks separate the coordinator, server ownership, maintenance ownership and
notification transport. Concurrent deliveries hold a shared transport lock through
receipt commit; snapshot maintenance acquires it exclusively outside any SQL write
transaction. Dead maintenance is recovered through kernel ownership rather than PID
expiry. Backups capture immutable copies of both SQLite stores and selected files,
then compress/publish atomically. They never advance a reconciliation target.

Task participant writes use SQLite transactions independently of the auxiliary
journal commit. A crash may leave an observed native effect without its receipt;
the existing before/after and read-set checks recover it rather than inventing
a cross-database transaction. There are no Taskwarrior subprocesses in normal
operation. An explicit offline legacy importer is the only code path that invokes
the old engine, takes a format-1 backup and publishes the converted store atomically.
New format-2 backups contain both portable SQLite stores; restoration checks
integrity, identity, dependency graphs, relations and durable authorization.

Linux cron/systemd and macOS launchd adapters execute the same bounded known-data tick.
Delivery policy, budgets, coalescing, suppression and backups are independent of LLM
availability. OS/harness interfaces remain adapters; there is no extra scheduler
daemon, global skill, SDLC coordinator, cloud sync or inbox integration.

## Task schema 3

Task UUIDs remain identities. `project` is the single stored membership list; the public
`groups` array and compatibility first `group` derive from it. A separate append-only
`aliases(number INTEGER PRIMARY KEY AUTOINCREMENT, uuid UNIQUE)` registry provides permanent
short display numbers. Alias allocation and task creation share one SQLite transaction;
capture Undo retires a row and preserves its alias. Aliases travel in SQLite backups and
new backup manifests check the mapping, while old manifests remain supported.

Migration uses the existing verified backup + revision/fingerprint coordinator protocol,
then one task-store transaction, rather than updating personal state from the UI. A failure
rolls back the transaction; no backup means no upgrade. Incomplete journals must settle first.
Historical fact plans are retained verbatim; Undo adapts their former scalar group to the
new representation at comparison time. Global rename/merge has one durable multi-participant
plan, recovery preconditions for every row, and a single inverse restoring all memberships
and colors. Read-only snapshots remain available for diagnosis, not mutation authorization.

`lastActive` records an actual previous start when a task leaves active work; `groupChanged`
records a membership assignment. Existing unknown history stays unknown. The public snapshot
exposes these instants and a derived persistent Undo stack without importing harness histories.
UI card identity is UUID plus section, so repeated group appearances do not collide during
DOM reuse, focus, animation or drag. Mode applies in a blocking same-origin script before
styles/paint under the existing CSP; palette and explicit mode are stored independently.
