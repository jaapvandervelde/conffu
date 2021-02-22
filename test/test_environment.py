import unittest
from conffu import Config
from os import environ, getenv, unsetenv, name as os_name


class TestConfig(unittest.TestCase):
    def setUp(self) -> None:
        # create test environment environment
        self.unset_vars = []
        self.save_environment = {}
        self.environment = {
            'a': '2', 'b': '1', 'c d': '4', 'e.f': '5', 't': 'text with spaces\nand newline', 'Z': '0'
        }

        for key, value in self.environment.items():
            if getenv(key) is None:
                self.unset_vars.append(key)
            else:
                self.save_environment[key] = getenv(key)
            environ[key] = value

    def tearDown(self) -> None:
        # restore environment
        for key in self.unset_vars:
            unsetenv(key)
        for key, value in self.save_environment.items():
            environ[key] = value

    def test_environment(self):
        cfg = Config({'t': ''}).update_from_environment()
        self.assertEqual(self.environment['t'], cfg['t'], msg='string values existing in env get updated')
        cfg = Config({'t': None}).update_from_environment()
        self.assertEqual(self.environment['t'], cfg['t'], msg='untyped values existing in env get updated as string')
        self.assertIsInstance(cfg['t'], str)
        cfg = Config({'c d': ''}).update_from_environment()
        self.assertEqual(self.environment['c d'], cfg['c d'], msg='string values with space existing in env updated')
        self.assertIsInstance(cfg['c d'], str)

    def test_environment_typed(self):
        cfg = Config({'a': 1}).update_from_environment()
        self.assertEqual(2, cfg['a'], msg='int values existing in env get updated')
        self.assertIsInstance(cfg['a'], int)
        cfg = Config({'a': 1.0}).update_from_environment()
        self.assertEqual(2.0, cfg['a'], msg='float values existing in env get updated')
        self.assertIsInstance(cfg['a'], float)
        cfg = Config({'b': False}).update_from_environment()
        self.assertEqual(True, cfg['b'], msg='bool values existing in env get updated')
        self.assertIsInstance(cfg['b'], bool)

    def test_environment_compound_keys(self):
        cfg = Config({'e': {'f': 1}}).update_from_environment()
        self.assertEqual(5, cfg['e.f'], msg='values with compound key existing in env get updated')
        cfg = Config({'e': {'f': 1}}, no_compound_keys=True).update_from_environment()
        self.assertEqual(5, cfg['e']['f'], msg='values with compound key existing in env get updated for non-comp')
        cfg = Config({'e.f': 1}, no_compound_keys=True).update_from_environment()
        self.assertEqual(5, cfg['e.f'], msg='values with compound key existing in env get updated for non-comp')
        cfg = Config({'e': {'f': 1}, 'e.f': 1}).update_from_environment()  # no_compound_keys=False
        self.assertEqual(5, cfg['e']['f'], msg='compound key preferred from env, if both provided to comp cfg')
        self.assertEqual(1, dict(cfg)['e.f'], msg='compound key preferred from env, if both provided to comp cfg')
        cfg = Config({'e': {'f': 1}, 'e.f': 1}, no_compound_keys=True).update_from_environment()
        self.assertEqual(5, cfg['e.f'], msg='non-compound key preferred from env, if both provided to non-comp cfg')
        self.assertEqual(1, cfg['e']['f'], msg='non-compound key preferred from env, if both provided to non-comp cfg')

    def test_windows_case_safe(self):
        # only test on Windows; TODO: rewrite test so that it also tests this on Linux
        if os_name == 'nt':
            cfg = Config({'A': 1}).update_from_environment()
            self.assertEqual(2, cfg['A'], msg='int values existing in env get updated, ignoring case (lower)')
            cfg = Config({'E': {'F': 1}}).update_from_environment()
            self.assertEqual(5, cfg['E.F'], msg='values with compound key existing in env get updated')
            cfg = Config({'z': 1}).update_from_environment()
            self.assertEqual(0, cfg['z'], msg='int values existing in env get updated, ignoring case (upper)')
        else:
            cfg = Config({'A': 1}).update_from_environment()
            self.assertEqual(1, cfg['A'], msg='int values existing in with mismatching case do no get updated, (lower)')
            cfg = Config({'e': {'f': 1}}).update_from_environment()
            self.assertEqual(5, cfg['e.f'], msg='values with compound key existing in env get updated')
            cfg = Config({'z': 1}).update_from_environment()
            self.assertEqual(1, cfg['z'], msg='int values existing in with mismatching case do no get updated, (upper)')

    def test_environment_add(self):
        cfg = Config({'x': 1}).update_from_environment(['a'])
        self.assertEqual(1, cfg['x'], msg='values not in environment are untouched')
        self.assertEqual('2', cfg['a'], msg='values specified for adding from environment are')
        self.assertEqual({'a': '2', 'x': 1}, dict(cfg), msg='only specified values are touched')

    def test_environment_exclude(self):
        cfg = Config({'a': 0, 'b': 0, 'e': {'f': 0}}).update_from_environment(exclude_vars=['a', 'e.f'])
        self.assertEqual({'a': 0, 'b': 1, 'e': {'f': 0}}, dict(cfg), msg='excluded variables are not touched')
        cfg = Config({'a': 0, 'b': 0, 'e': {'f': 0}}).update_from_environment(exclude_vars=['a', 'e'])
        self.assertEqual({'a': 0, 'b': 1, 'e': {'f': 5}}, dict(cfg),
                         msg='excluded sub-variables can be touched when specifically targeted')
        cfg = Config({'a': 0, 'b': 0, 'c': 0}).update_from_environment(['a', 'b'], exclude_vars=['b'])
        # c remains 0 because it is not specified, b remains 0 because it is excluded
        self.assertEqual({'a': 2, 'b': 0, 'c': 0}, dict(cfg), msg='exclusion overrides specified values')
