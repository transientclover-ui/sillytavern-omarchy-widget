# Local validation — 2026-10-11

**Verified environment: Frankenstein KDE Plasma Wayland with the preserved Omarchy
bar. This report does not establish live Hyprland or filtered-adapter support.**

Tested on Arch Linux, KDE Plasma Wayland with the preserved Omarchy Quickshell
bar and Frankenstein integration. AMD RX 5700, 8 GB VRAM, 16 GB system memory.

## Automated and integration results

- Three automated tests pass: readiness/false-positive cases, argument validation,
  and isolated installation/update/uninstall preserving configuration and layout.
- `systemd-analyze --user verify` passes for the generated inference unit.
- `desktop-file-validate` passes for both RP AI launchers.
- Real user-manager integration with the health fixture exercised STARTING → READY
  → OFF and missing-binary ERROR. A live bar IPC query confirmed READY.
- Five repeated starts with the fixture kept the same PID.
- The real llama.cpp server was launched through the ON .desktop launcher and
  stopped through the OFF .desktop launcher.
- Eight concurrent ON requests kept exactly the same real inference PID.
- Real socket ownership + `/health` returned READY. Vulkan backend library was
  mapped in the server. A 33-token chat completion ran at about 56 tokens/second;
  this is a short smoke test, not a benchmark.
- SillyTavern 1.19.0 (release commit 06bde93) loaded in the browser, connected via
  Text Completion / llama.cpp, and generated a fantasy tavern greeting.
- OFF stopped the real inference service; SillyTavern still returned HTTP 200.
- User service is `static` with no login enablement. Final inference state is OFF.
- Installer updates did not overwrite local model/port configuration.
- Port 8080 was already occupied. Startup failed visibly instead of starting a
  duplicate or stopping the existing listener. Local configuration uses 18080.

Display labels are Offline (OFF), Partial (STARTING), Online (READY), and Error
(ERROR). Final live QML label queries observed Partial → Online → Offline. The CLI and widget tooltip retain the exact service/readiness states.

## Installed dependencies

Official llama.cpp b11557 Vulkan x64 release archive:
`sha256:c05ccb11f6de7c907c9ca861a0bb921bc3a52a94912cd0f1d47d53cea0c3dc08`.

Stheno 3.4 8B Q4_K_M GGUF from bartowski's model repository, revision
`c723084e4438dc763cd01ea6ac78754946dba48f`:
`sha256:ca635b6dad84f3d093ab5cf93d88e809d8d5e6e7e1729cf94e597e46e69d6793`.
Both downloaded files were checked against upstream metadata before use.
Dependencies/model are installed locally and are not part of this repository.

## Limits

No live normal Omarchy Hyprland, Frankenstein Hyprland, or filtered Plasma adapter
session was available for runtime testing. Their compatibility is based on the
shared plugin interface and source inspection. No session switching, logout,
reboot, full-context stress test or long roleplay-quality assessment was performed.
No framebuffer screenshot of the desktop bar was captured; live widget IPC verifies
its instantiated QML state. See COMPATIBILITY.md for the target matrix.

The separate local Butler stop companion was tested with an isolated matching
executable and an unrelated process: only the matching process stopped. A dry run
matched the real installed Butler; the running Butler application was left open.
