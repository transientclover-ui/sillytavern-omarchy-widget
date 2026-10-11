# SillyTavern Omarchy Widget

A compact **RP AI Offline / Partial / Online / Error** bar widget and separate
**RP AI ON** and **RP AI OFF** application launchers for a local llama.cpp server.
SillyTavern remains an independent frontend. This project is not affiliated with
SillyTavern, Omarchy, Frankenstein, or llama.cpp.

One user service, `rp-ai.service`, owns inference across desktop sessions and
monitors. The project never enables it at login, downloads a model, or starts
inference during installation. No root permissions are needed.

## Requirements

Arch Linux, Python 3, systemd user manager, an installed llama.cpp `llama-server`,
a local GGUF model, and the current Omarchy Quickshell plugin API (`qs.Ui.BarWidget`
and `WidgetButton`). `notify-send` is optional for control-error notifications.
`desktop-file-validate` is required for the packaging tests.
The Omarchy bar must already be running. A native KDE panel alone cannot host this
widget; enable the optional Omarchy bar through your existing Frankenstein setup.
The frontend and inference engine are **not bundled or licensed by this project**.

## Install and configure

```sh
python3 install.py install
# Or install launchers without changing the bar:
python3 install.py install --no-bar
```

Edit `~/.config/rp-ai/config.json` using `config.example.json` as the schema.
Set absolute `binary` and `model` paths, an unused loopback port, context size,
and GPU offload flags appropriate for your GPU. Paths containing spaces work;
`args` is a JSON string array, never evaluated by a shell. Host is restricted to
`127.0.0.1`. Router mode, endpoint/model overrides in `args`, and sleep mode are
unsupported because they invalidate the single loaded-model readiness contract.
Stop inference before editing its configuration. Installation does not configure
SillyTavern or alter its data.

Click **RP AI ON**, wait for **Online**, then connect SillyTavern using
**Text Completion → llama.cpp** and `http://127.0.0.1:<configured-port>`.
Click **RP AI OFF** to unload inference. SillyTavern stays open.

The installed CLI is `~/.local/share/rp-ai/rp-ai`:

```sh
~/.local/share/rp-ai/rp-ai on
~/.local/share/rp-ai/rp-ai off
~/.local/share/rp-ai/rp-ai status --json
```

The single widget ID is `local.rp-ai`. The installer adds it to the right section
without replacing other entries. To allow click-to-toggle, set `clickToToggle`
to `true` on that entry in `~/.config/omarchy/shell.json`. It defaults to false.
The widget polls every two seconds and shares the same service as both launchers.
Stock plugin discovery uses `~/.config/omarchy/plugins`; alternate XDG paths
require a shell that supports those paths.

The familiar display labels map OFF → Offline, STARTING → Partial, and READY → Online.
ERROR displays Error. The tooltip and CLI keep the precise underlying state.

## What the states mean

| State | Evidence |
|---|---|
| OFF | Service inactive or stopping; stopping is explained in the tooltip |
| STARTING | Service starting/running, waiting for the model's `/health` response |
| READY | Service MainPID owns the listening socket and `/health` returns HTTP 200 with `status: ok` |
| ERROR | Failed/missing service, bad configuration, another process on the endpoint, invalid health response, or startup timeout |

Readiness uses Linux `/proc` socket ownership, not a saved toggle preference or
port ping. The service PID is rechecked after the health request. A startup timeout
reports ERROR but leaves the process available for inspection; OFF stops it.
No request to generate text is made by the widget.

Repeated ON requests use the same systemd service. Control/toggle operations are
serialized, and the server holds a separate inherited file lock. Startup refuses
an occupied port or an existing same-user `llama-server` process instead of killing
unmanaged servers. Another user's process on a different port is outside scope.
An unrelated process started independently can still race startup; its occupied
port causes bind failure rather than readiness. To migrate an old server, stop
and disable its old unit/autostart yourself before using RP AI ON.

## Update and uninstall

Run the installer from the updated checkout again. Existing `config.json`, widget
placement/settings, and other shell configuration are preserved. Managed program,
plugin, unit, and launcher files are replaced, with prior files backed up under
`~/.local/state/rp-ai/backups/<timestamp>/`. A running model is not restarted by an
update. Stop it before changing binary/model settings.

```sh
python3 install.py uninstall
```

Uninstall stops only `rp-ai.service`, removes its widget entry and managed files,
and preserves inference configuration and backups. It never removes models,
llama.cpp, or SillyTavern. To undo a layout change manually, compare the backup with
the current `shell.json` and restore only the relevant entry, preserving later
edits. The installer supports XDG_CONFIG_HOME, XDG_DATA_HOME and XDG_STATE_HOME.

## Troubleshooting and tests

```sh
journalctl --user -u rp-ai.service -n 50
systemctl --user show rp-ai.service -p ActiveState -p MainPID -p Result
python3 -m unittest discover -s tests -v
```

Tests cover readiness including false-positive HTTP responses, argument validation,
install/update/uninstall, preserved custom config/layout, paths containing spaces,
.desktop validation and lack of autostart. `tests/fake-server.py` is a health fixture
for local integration testing, not an inference engine.

See [compatibility](docs/COMPATIBILITY.md) and [local validation](docs/VALIDATION.md).
MIT applies only to this project's original code. Third-party dependencies and
model weights retain their respective licenses.
