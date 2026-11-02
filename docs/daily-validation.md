# Validation scope

The public source includes executable checks, not captured operator run evidence.
Use the README commands from a clean source directory and disposable private state.
Core discovery uses real SQLite stores and controlled subscription fixtures.
English is the default; Spanish tests exercise optional UI strings and content
preservation. No fixture proves a live model, subscription login or native Mac deployment.

The separate Linux system suite requires D-Bus, libnotify, PyGObject and GLib/Gio
as declared in the README. It starts a private bus and synthetic notification
server; discovery deliberately skips it. Set `E2E_REPORT_DIR` outside the checkout
for private logs. Do not publish generated journals, task captures or credentials.

Optional legacy import/parity cases require an explicitly selected Taskwarrior
3.5.0 executable. Optional browser tests require an installed compatible
`chrome-devtools-axi`; optional pure ordering tests use Node.js 18+. Missing
optional tools produce skips, not evidence of execution.

There are no distributed screenshots or historical PR attachments. Any future
image needs synthetic provenance and a human visual review before publication.
Linux core checks do not establish macOS notification permissions, sleep behavior,
remote exposure, live-model semantics or physical-device usability.
