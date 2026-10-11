import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.machinery.SourceFileLoader('rp_ai', str(ROOT / 'bin/rp-ai'))
spec = importlib.util.spec_from_loader(loader.name, loader)
rp = importlib.util.module_from_spec(spec)
loader.exec_module(rp)


class Readiness(unittest.TestCase):
    def state(self, active='active', code=None, owned=False, body=None, elapsed=1, result='success', load='loaded'):
        return rp.classify({'ActiveState': active, 'Result': result, 'LoadState': load}, code, body or {}, owned, elapsed, 30)[0]

    def test_states_and_false_readiness(self):
        self.assertEqual(self.state(active='inactive'), 'OFF')
        self.assertEqual(self.state(), 'STARTING')
        self.assertEqual(self.state(code=503, owned=True), 'STARTING')
        self.assertEqual(self.state(code=200, owned=True, body={'status': 'ok'}), 'READY')
        self.assertEqual(self.state(code=200, body={'status': 'ok'}), 'ERROR')
        self.assertEqual(self.state(code=200, owned=True, body={'status': 'sleeping'}), 'ERROR')
        self.assertEqual(self.state(elapsed=31), 'ERROR')
        self.assertEqual(self.state(active='failed', result='exit-code'), 'ERROR')
        self.assertEqual(self.state(load='not-found'), 'ERROR')
        self.assertEqual(self.state(code=500, owned=True), 'ERROR')

    def test_config_argument_safety(self):
        with tempfile.TemporaryDirectory() as d:
            old = rp.CONFIG
            rp.CONFIG = Path(d) / 'config.json'
            try:
                c = {'binary': '/tmp/server', 'model': '/tmp/model with spaces.gguf', 'args': ['--port=9999']}
                rp.CONFIG.write_text(json.dumps(c))
                with self.assertRaises(ValueError):
                    rp.config()
                c['args'] = ['--ctx-size', '2048']
                rp.CONFIG.write_text(json.dumps(c))
                self.assertEqual(rp.config()['model'], c['model'])
            finally:
                rp.CONFIG = old


class Lifecycle(unittest.TestCase):
    def test_install_update_remove_preserve_user_data(self):
        with tempfile.TemporaryDirectory(prefix='rp ai ') as d:
            env = dict(os.environ, HOME=d, XDG_CONFIG_HOME=d + '/.config', XDG_DATA_HOME=d + '/.local/share', XDG_STATE_HOME=d + '/.local/state')
            shell = Path(d) / '.config/omarchy/shell.json'
            shell.parent.mkdir(parents=True)
            initial = {'bar': {'layout': {'right': [{'id': 'other', 'custom': 42}]}}, 'disabledPlugins': ['omarchy.background']}
            shell.write_text(json.dumps(initial))
            def invoke(action):
                subprocess.run(['python3', str(ROOT / 'install.py'), action, '--no-systemd'], env=env, check=True, capture_output=True)
            invoke('install')
            config = Path(d) / '.config/rp-ai/config.json'
            config.write_text('{"custom": "preserve me"}\n')
            cfg = json.loads(shell.read_text())
            cfg['bar']['layout']['right'][-1]['clickToToggle'] = True
            shell.write_text(json.dumps(cfg))
            invoke('install')
            self.assertEqual(config.read_text(), '{"custom": "preserve me"}\n')
            entries = json.loads(shell.read_text())['bar']['layout']['right']
            self.assertEqual(len(entries), 2)
            self.assertTrue(entries[-1]['clickToToggle'])
            for f in (Path(d) / '.local/share/applications').glob('*.desktop'):
                subprocess.run(['desktop-file-validate', str(f)], check=True)
            unit = Path(d) / '.config/systemd/user/rp-ai.service'
            self.assertNotIn('[Install]', unit.read_text())
            invoke('uninstall')
            self.assertEqual(json.loads(shell.read_text())['bar']['layout']['right'], initial['bar']['layout']['right'])
            self.assertEqual(json.loads(shell.read_text())['disabledPlugins'], ['omarchy.background'])
            self.assertTrue(config.exists())
            self.assertFalse(unit.exists())
            self.assertTrue(list((Path(d) / '.local/state/rp-ai/backups').rglob('shell.json')))


if __name__ == '__main__':
    unittest.main()
