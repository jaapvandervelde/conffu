import unittest
import inspect
import tempfile
from pathlib import Path
from conffu import Config


class TestConfig(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self._cfg = Config({
            "_globals": {
                "foo": "bar"
            },
            "baz": "qux {foo}",
            "quux": {
                "corge": "grault {foo}"
            },
            "garply": {
                "waldo": 1,
                "fred": ["plugh", "xyzzy", "{foo}", "{{foo}}"]
            },
            "thud": 42.0
        })

    def tearDown(self):
        self.tmpdir.cleanup()

    def _check_config(self, cfg):
        context = inspect.stack()[1][3]
        self.assertTrue(cfg.globals)
        self.assertIn('foo', cfg.globals, f'_globals foo should have foo ({context})')
        self.assertEqual('bar', cfg.globals['foo'], f'_globals foo should be bar ({context})')
        self.assertIn('baz', cfg, 'baz should be in config ({context})')
        self.assertEqual('qux bar', cfg.baz, f'baz should be qux bar after subst ({context})')
        self.assertIn('quux', cfg, 'quux should be in config ({context})')
        self.assertIn('corge', cfg.quux, 'quux should be in quux ({context})')
        self.assertEqual('grault bar', cfg.quux.corge, f'quux.corge should be qux bar after subst ({context})')
        self.assertIn('garply', cfg, 'garply should be in config ({context})')
        self.assertIn('waldo', cfg.garply, 'waldo should be in garply ({context})')
        self.assertEqual(1, cfg.garply.waldo, f'garply.waldo should be 1 (int) ({context})')
        self.assertIn('fred', cfg.garply, 'fred should be in garply ({context})')
        self.assertEqual(['plugh', 'xyzzy', 'bar', '{foo}'], cfg.garply.fred,
                         f'garply.fred should be ["plugh", "xyzzy", "bar", "{{foo}}"] (list) ({context})')
        self.assertEqual(42.0, cfg.thud, f'thud should be 42.0 (float) ({context})')

    def test_json_roundtrip(self):
        self._cfg.save(Path(self.tmpdir.name) / 'config_copy.json')
        cfg = Config.from_file(Path(self.tmpdir.name) / 'config_copy.json')
        self._check_config(cfg)
        self.assertEqual(cfg, self._cfg)

    def test_xml_roundtrip(self):
        self._cfg.save(Path(self.tmpdir.name) / 'config_copy.xml')
        cfg = Config.from_file(Path(self.tmpdir.name) / 'config_copy.xml')
        self._check_config(cfg)
        self.assertEqual(cfg, self._cfg)

    def test_pickle_roundtrip(self):
        self._check_config(self._cfg)
        self._cfg.save(Path(self.tmpdir.name) / 'config_copy.pickle')
        cfg = Config.from_file(Path(self.tmpdir.name) / 'config_copy.pickle')
        self._check_config(cfg)
        self.assertEqual(cfg, self._cfg)
