#!/usr/bin/env python3
"""User-only install/update/uninstall; preserve inference configuration."""
import argparse
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
CFG = Path(os.environ.get('XDG_CONFIG_HOME', HOME / '.config'))
DATA = Path(os.environ.get('XDG_DATA_HOME', HOME / '.local/share'))
STATE = Path(os.environ.get('XDG_STATE_HOME', HOME / '.local/state')) / 'rp-ai'
APP = DATA / 'rp-ai'
PLUGIN = CFG / 'omarchy/plugins/local.rp-ai'
UNIT = CFG / 'systemd/user/rp-ai.service'
SHELL = CFG / 'omarchy/shell.json'
STAMP = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')


def atomic(path, text, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.rp-ai.tmp')
    temp.write_text(text)
    temp.chmod(mode)
    temp.replace(path)


def backup(path):
    if path.exists():
        dst = STATE / 'backups' / STAMP / path.relative_to(HOME)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)


def desktop_quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%') + '"'


def unit_quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%') + '"'


def shell_edit(remove=False):
    c = json.loads(SHELL.read_text()) if SHELL.exists() else {'version': 1}
    layout = c.setdefault('bar', {}).setdefault('layout', {})
    found = False
    for section in ('left', 'center', 'right'):
        entries = layout.setdefault(section, [])
        found |= any(e.get('id') == 'local.rp-ai' for e in entries)
        if remove:
            layout[section] = [e for e in entries if e.get('id') != 'local.rp-ai']
    if not remove and not found:
        layout['right'].append({'id': 'local.rp-ai', 'clickToToggle': False})
    backup(SHELL)
    atomic(SHELL, json.dumps(c, indent=2) + '\n')


def install(bar=True, systemd=True):
    if UNIT.exists() and 'Description=Manual RP AI llama.cpp inference server' not in UNIT.read_text():
        raise RuntimeError(f'Refusing to overwrite unrelated unit: {UNIT}')
    # Validate layout before any changes.
    if bar and SHELL.exists():
        json.loads(SHELL.read_text())
    for target in (APP / 'rp-ai', UNIT, PLUGIN / 'BarWidget.qml', PLUGIN / 'manifest.json'):
        backup(target)
    atomic(APP / 'rp-ai', (ROOT / 'bin/rp-ai').read_text(), 0o755)
    config = CFG / 'rp-ai/config.json'
    if not config.exists():
        atomic(config, (ROOT / 'config.example.json').read_text(), 0o600)
    atomic(UNIT, '# Managed by sillytavern-omarchy-widget\n[Unit]\nDescription=Manual RP AI llama.cpp inference server\n\n[Service]\nType=exec\nExecStart=' + unit_quote(APP / 'rp-ai') + ' run\nRestart=no\nKillMode=control-group\nTimeoutStopSec=20\nEnvironment=' + unit_quote('XDG_CONFIG_HOME=' + str(CFG)) + '\n\n# No Install section: never starts automatically at login.\n')
    for name in ('BarWidget.qml', 'manifest.json'):
        atomic(PLUGIN / name, (ROOT / 'plugin' / name).read_text())
    # Absolute symlink avoids PATH assumptions in desktop shells.
    link = PLUGIN / 'rp-ai'
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(APP / 'rp-ai')
    for action in ('on', 'off'):
        target = DATA / f'applications/rp-ai-{action}.desktop'
        backup(target)
        atomic(target, '[Desktop Entry]\nType=Application\nName=RP AI ' + action.upper() + '\nComment=' + ('Start' if action == 'on' else 'Stop') + ' local llama.cpp inference\nExec=' + desktop_quote(APP / 'rp-ai') + ' ' + action + '\nIcon=' + ('media-playback-start' if action == 'on' else 'media-playback-stop') + '\nTerminal=false\nCategories=Utility;\nStartupNotify=false\n')
    if bar:
        shell_edit()
    if systemd:
        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
    print(f'Installed. Configure {config}. Inference was not started or enabled. Backups: {STATE / "backups"}')


def uninstall(systemd=True):
    if systemd:
        subprocess.run(['systemctl', '--user', 'stop', 'rp-ai.service'], check=True)
    if SHELL.exists():
        shell_edit(remove=True)
    for target in (APP, PLUGIN):
        if target.exists():
            shutil.rmtree(target)
    for target in (UNIT, DATA / 'applications/rp-ai-on.desktop', DATA / 'applications/rp-ai-off.desktop'):
        target.unlink(missing_ok=True)
    if systemd:
        subprocess.run(['systemctl', '--user', 'daemon-reload'], check=True)
        subprocess.run(['systemctl', '--user', 'reset-failed', 'rp-ai.service'], check=False, capture_output=True)
    print(f'Removed. Preserved configuration at {CFG / "rp-ai"} and backups at {STATE}.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=['install', 'uninstall'])
    ap.add_argument('--no-bar', action='store_true', help='Install controller/launchers without changing bar layout')
    ap.add_argument('--no-systemd', action='store_true', help='For isolated packaging tests only')
    a = ap.parse_args()
    if a.action == 'install':
        install(not a.no_bar, not a.no_systemd)
    else:
        uninstall(not a.no_systemd)
