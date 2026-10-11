# Compatibility matrix

| Target | Controller and launchers | Widget | Verification |
|---|---|---|---|
| Frankenstein KDE Plasma Wayland, preserved stock Omarchy shell | Supported | Supported | Live user service and loaded widget tested on this machine |
| Normal Omarchy Hyprland | Designed to work | Same stock bar API; no compositor imports in widget | Not tested in a live Hyprland session |
| Frankenstein Hyprland | Designed to work | Same stock bar API | Not tested in a live Hyprland session |
| Frankenstein KDE filtered adapter with optional Omarchy bar | Designed to work | Third-party plugins are not restricted by its first-party allowlist | Adapter source inspected; not exercised live |
| KDE with native Plasma panel only | Supported | No Omarchy bar available | Requires existing optional Omarchy bar; installer does not enable it |
| Older Waybar-based Omarchy | Supported | Quickshell plugin unavailable | Not supported for widget; no Waybar module shipped |

The observed desktop is KDE / Wayland. Only that available session was exercised;
no login/session switching was performed. No Frankenstein source files were changed.
The preserved stock shell uses `/usr/share/omarchy/shell`; the filtered adapter's
PluginRegistry was inspected at `/usr/share/frankenstein/omarchy-shell/services/PluginRegistry.qml`.
Both discover configured third-party plugins in the user plugin directory. The
widget imports no Hyprland API and controls no compositor-specific functionality.

Inference lives in one user manager, not in a graphical-session service. Its unit
has no `WantedBy`, `PartOf`, or `Install` section. Moving between supported sessions
therefore does not create another server. A logout that terminates the user's
systemd manager will stop inference; the project never enables user lingering.
