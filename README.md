# Day Attendant

A local assistant for personal responsibilities: tasks, calendar commitments,
blocking prerequisites, related work, snoozes, remaining effort and continuity.
A browser UI and CLI share a Python/SQLite coordinator. Typed changes work without
an LLM; optional subscription harnesses interpret conversation and suggest next steps.
The model cannot write directly to the task store.

## Required versus optional tools

- Python **3.11+**, including standard-library `sqlite3` and `zoneinfo`.
  The export is checked on Python 3.11.2 / SQLite 3.40.1; use SQLite **3.35+**.
- IANA timezone data, including `UTC` and any zone you select. On Linux this is the
  operating system's `tzdata` package (this export used **2026e**);
  macOS supplies system zone data. Missing zones produce an explicit error.
- A modern browser for the UI. The core CLI needs no browser or JavaScript runtime.
- Optional inference: an authenticated **Codex CLI** with app-server structured
  output (protocol fixture baseline **0.164.0**) or **Claude Code** with restricted
  safe-mode structured print sessions (protocol fixture baseline **2.1.312**).
  These versions identify adapter contracts, not live validation of this export.
  Unsupported/authentication/quota failures are visible; there is no provider,
  account, model or paid API fallback. You install and authenticate a harness
  separately. No API key, MCP server or extra Python package is needed by the core.
- Optional native reminders: Linux `notify-send` / libnotify **0.8+**, a desktop
  notification server on the user's D-Bus session, and systemd user services
  (**252+**) or cron (**3.x**) for explicit scheduling. macOS uses system-provided
  `osascript` and launchd. Missing delivery/scheduler tools are reported; tasks
  and manual backups keep working. No scheduler is installed on first run.

From the source root, run this read-only inventory using already approved tools:

```sh
python3 -B scripts/check_tools.py
```

If `python3` itself is absent, the shell reports that before the check can run.
The READY result covers required core capabilities only; optional features and
selected timezone data need separate verification. Tool versions may be unknown.

## Anonymize mode

Use **Anonymize** in the header (**Anonimizar** in Spanish) before a screenshot.
It starts off, remembers its state only in this tab's `sessionStorage`, and
restores current real text when turned off. The tab title stays unchanged; there
is no extra banner or lock icon.

A local DOM observer replaces unknown text, tooltips, accessible labels,
placeholders and form values, including hidden panels, errors, diagnostics,
conversation, filenames and later content. Interface copy comes from the existing
translation catalogs; interpolated data is masked. Explicitly typed counts,
progress, states and dates remain visible. A free-text numeric title is masked.
Neutral replacements follow the interface language and measured word widths.
Large updates keep the page invisible, preserving its layout, while frame-sized
batches finish. Data controls are read only and submissions/write deliveries are
blocked, so replacement text cannot be saved as real data.

This is a screenshot aid, **not a privacy guarantee**. Browser chrome/tabs,
images, canvas, CSS pseudo-elements, iframes and embedded content are outside its
scope. URLs, internal attributes, logs and network traffic retain real values.
Open shadow roots and SVG text are processed; inaccessible closed roots are not.
Native controls keep their outer bounds but may wrap replacement text differently;
complex bidi, ligatures, soft hyphens, variable fonts and unusual CSS also need
visual review. Check the whole screenshot before sharing it.

The existing Chrome AXI/SQLite fixture checks canaries, visible frames,
restoration, two viewports/fonts, line counts, block geometry (2%) and 500/2,000-row
performance. It runs in `unittest` when Chrome AXI is available, or separately:

```sh
python3 -B scripts/test_anonymize_ui.py --out /tmp/day-anonymize-proof
```

## macOS

Linux is verified. macOS is supported by design but is not accepted until the
inventory and documented tests have run on the target Mac. Native permissions,
notifications, scheduling and sleep/resume require separate Mac checks. Use only
already approved tools; no root or new dependencies are required for core use.
Temporary files use the standard temporary directory and respect `TMPDIR` when
it names a writable directory. The Linux system suite below is Linux-only.

## Install and start

Unpack the reviewed source into a user-owned directory. Keep the entire directory,
including `day_attendant/ui`; run these commands from its root. This is a source
installation: no package download, compilation, administrator access or pip step
is required. Keep this directory at a stable location while its service is running.

```sh
python3 -B day-attendant.py init --zone UTC --name 'My responsibilities'
python3 -B day-attendant.py service start
python3 -B day-attendant.py service status
python3 -B day-attendant.py --json board list
python3 -B day-attendant.py service open
```

A new personal profile is empty. `service open` prints a private session URL and
attempts to open your browser; if no browser is available, open that URL yourself.
Treat it as a credential. Without Codex/Claude, typed tasks, calendar, relationships,
local known-data rules and backups work. Chat, model follow-up and suggested order
show their unavailable status. Starting a service sends no inference turn.

On Linux, private state is `day-attendant/profiles/default` inside the user
state directory selected by `XDG_STATE_HOME`; that directory defaults to
`.local/state` inside the home directory. On macOS, state is
`Library/Application Support/Day Attendant/profiles/default` inside the home directory.
`DAY_ATTENDANT_STATE` or the global `--state` option selects another directory
**outside the source checkout**. The service manages `tasks.sqlite3`,
`assistant.sqlite3`, attachments and credentials. Do not edit either database.

## Configuration and language

The UI and new profiles default to English. Settings select English or Spanish,
timezone, harness/model/effort, reminder policy and backup location. Existing card
and conversation text keeps its creation language. Conversation follows the user's
language; follow-up and order suggestions follow the profile locale. CLI authored
copy defaults to English and supports the per-invocation `--lang es` option;
structured JSON keys and some diagnostic details remain English.

These changes select Spanish, inspect it, then return the installation to English:

```sh
python3 -B day-attendant.py profile configure --values '{"locale":"es"}' --key readme-locale-es-001
python3 -B day-attendant.py --lang es profile show
python3 -B day-attendant.py profile configure --values '{"locale":"en"}' --key readme-locale-en-001
```

The shared prompt has no personal recipient. Optionally set
`DAY_ATTENDANT_RECIPIENT` in your private process environment **before starting
or restarting the service**. It is a form of address, separate from the profile
label. Empty, over-100-character or control-character values use the neutral default.
For example, this explicitly synthetic value can be replaced locally:

```sh
export DAY_ATTENDANT_RECIPIENT='[SYNTHETIC] Example Stargazer'
```

Never commit installation environments, profiles, credentials or real captures.
Task writes use UUIDs, stable request keys and observed revisions. See the
[operation guide](docs/daily-operation.md) for actions, recovery and reminders.

## Backup and recovery

Manual snapshots coherently include both databases and selected attachments,
excluding harness authentication and HTTP credentials. Store copies on an
independent private device to protect against disk loss. This example creates,
verifies and restores a snapshot into a **new** directory; preserve the shell
variable within this block:

```sh
ARCHIVE="$(python3 -B day-attendant.py --json backup create --key readme-backup-001 | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["path"])')"
python3 -B day-attendant.py backup verify "$ARCHIVE"
python3 -B day-attendant.py backup list
python3 -B day-attendant.py service stop
RESTORED_PROFILE="$(python3 -c 'from pathlib import Path; print(Path.home().joinpath("day-attendant-restored"))')"
python3 -B day-attendant.py restore "$ARCHIVE" --to "$RESTORED_PROFILE"
```

Use a previously unused restore destination. Restore is offline, refuses an
occupied directory, changes profile identity, invalidates pending reasoning and
disables reminders. It installs no jobs. Select a restored directory explicitly
only after reviewing it. An interrupted operation may open a diagnostic read
view; preserve it and use supervised `reconcile`, never force an overwrite.
Schema upgrades require a verified backup. The one-time optional legacy importer
requires an existing **Taskwarrior 3.5.0** executable; Taskwarrior is never the
runtime backend. Old files are preserved. See the operation guide.

## Security and network access

The HTTP service binds only to the IPv4 loopback interface, uses a private bearer/session token,
checks Host/Origin on requests and owns one service per profile. Private profile
files use restricted permissions. Session credentials are persisted for reopening
and address reuse; avoid sharing URLs, logs, snapshots or screenshots. There is
no public bind setting, cloud upload, inbox integration or automatic device sync.

For deliberate access from another machine, an operator can forward the service's
loopback port through an independently authenticated SSH tunnel, using the same
loopback port and URL on the client to preserve origin checks. Keep the session
token private and do not bind the forwarded port to a public interface. The
operator supplies and secures that transport; remote exposure and reverse-proxy
configurations are outside this export's tested support.

## Tests

From the source root:

```sh
python3 -B -m unittest discover -s tests -q
python3 -B scripts/test_system.py
python3 -B scripts/demo.py
```

Discovery exercises real disposable SQLite stores, recovery, backup/restore,
concurrency, CLI/HTTP boundaries, languages and controlled harness protocols.
It skips Linux D-Bus system scenarios (run separately), optional legacy comparisons
without the explicitly selected old binary, and optional executable UI tests when
`chrome-devtools-axi` is absent. Node.js **18+** enables the optional pure ordering
rule test (checked with 22.23.4). UI tests additionally require the separately
supplied `chrome-devtools-axi` interface and compatible Chromium; this export
makes no standalone browser installation or physical-device validation claim.

The Linux system suite requires D-Bus **1.14+**, `notify-send` **0.8+**,
PyGObject **3.42+** and GLib/Gio **2.74+**, plus normal OS user-account
lookup and a machine ID. Minimal test sandboxes must supply a synthetic account
and machine ID rather than mount operator identity files. It creates a private session bus with a
synthetic notification server, never uses the desktop bus and never installs jobs.
Its evidence defaults to a temporary directory; `E2E_REPORT_DIR` chooses a private
output folder. The demo uses disposable, explicitly synthetic tasks. Neither
command calls a model. See [validation scope](docs/daily-validation.md).

## Limits

Linux core behavior is validated locally. macOS shares the SQLite backend but
requires real deployment, native notification and sleep/resume checks; see the
[Mac handoff](docs/macos-handoff.md). Windows, multi-user hosting, public Internet
hosting, unattended LLM turns, cloud sync and automatic source ingestion are not
supported. Reminder receipts do not prove a person read a notification. No test
claims perfect planning, risk detection or psychological outcomes.

No screenshots, historical run traces, personal tasks or attachments ship in this
export. All authored demo/test data is synthetic. The original [LICENSE](LICENSE)
and any attribution in it are preserved unchanged.

Theme colors are adapted from MIT-licensed palettes; see [THEMES-LICENSES.md](THEMES-LICENSES.md).
