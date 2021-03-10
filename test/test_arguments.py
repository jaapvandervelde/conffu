import unittest
from conffu import Config
# noinspection PyProtectedMember
from conffu._config import argv_to_dict
from io import StringIO
from os import name as os_name

class TestConfig(unittest.TestCase):
    def test_argv_to_dict_no_arguments(self):
        args = argv_to_dict(['script.py'])
        self.assertEqual({'': ['script.py']}, args, msg='empty argv should result in empty arguments dict')

    def test_argv_to_dict_simple_arguments(self):
        args = argv_to_dict(['script.py', 'arg.1', 'arg.2'])
        self.assertEqual({'': ['script.py', 'arg.1', 'arg.2']}, args, msg='simple arguments should be in empty key')

    def test_argv_to_dict_switch_argument(self):
        args = argv_to_dict(['script.py', '-a', '--b', '/c', '//', '---', '/--'])
        if os_name == 'nt':
            self.assertEqual({'': ['script.py'], 'a': [], 'b': [], 'c': [], '/': [], '-': [], '--': []}, args,
                             msg='switch argument with -/--// should get own key')
        else:
            self.assertEqual({'': ['script.py'], 'a': [], 'b': ['/c', '//'], '-': ['/--']}, args,
                             msg='switch argument with -/-- should get own key')

    def test_argv_to_dict_aliases(self):
        if os_name == 'nt':
            args = argv_to_dict(['script.py', '-ax', '--bxx', '/c-'], aliases={'ax': 'a', 'bxx': 'b', 'c-': 'c'})
            self.assertEqual({'': ['script.py'], 'a': [], 'b': [], 'c': []}, args,
                             msg='switch argument should get mapped to alias')
        else:
            args = argv_to_dict(['script.py', '-ax', '--bxx', '-c-'], aliases={'ax': 'a', 'bxx': 'b', 'c-': 'c'})
            self.assertEqual({'': ['script.py'], 'a': [], 'b': [], 'c': []}, args,
                             msg='switch argument should get mapped to alias')

    def test_argv_to_dict_parameters(self):
        args = argv_to_dict(['script.py', '-a', '1', '2', '--bb', 'a b  c '], aliases={'bb': 'b'})
        self.assertEqual({'': ['script.py'], 'a': ['1', '2'], 'b': ['a b  c ']}, args,
                         msg='switch argument parameters get assigned to argument')

    def test_config_compound_key(self):
        cfg = Config({'a': {'b': 'foo'}})
        self.assertEqual(cfg['a.b'], 'foo', msg='vales in nested configuration should be accessible by compound key')

    def test_global_argument(self):
        args = argv_to_dict(['script.py', '-{root}', 'foo', '-p', '{root}/bar'])
        cfg = Config().update_from_arguments(args)
        self.assertEqual(cfg['p'], 'foo/bar', msg='argument without parameters should be True in Config')

    def test_config_argument(self):
        args = argv_to_dict(['script.py', '-a'])
        cfg = Config().update_from_arguments(args)
        self.assertEqual(cfg['a'], True, msg='argument without parameters should be True in Config')

    def test_config_argument_full_update(self):
        args = argv_to_dict(['script.py', '-a'])
        cfg = Config().full_update(cli_args=args)
        self.assertEqual(cfg['a'], True, msg='argument without parameters should be True in Config')

    def test_config_argument_parameter(self):
        args = argv_to_dict(['script.py', '-a', '1'])
        cfg = Config().update_from_arguments(args)
        self.assertEqual(cfg['a'], '1', msg='argument with single parameter should be single value in Config')

    def test_config_argument_parameters(self):
        args = argv_to_dict(['script.py', '-a', '1', '2'])
        cfg = Config().update_from_arguments(args)
        self.assertEqual(cfg['a'], ['1', '2'], msg='argument with multiple parameters should be list in Config')

    def test_config_compound_key_argument(self):
        args = argv_to_dict(['script.py', '-a.b', 'foo'])
        cfg = Config({'a': {'b': 'bar'}}).update_from_arguments(args)
        self.assertEqual(cfg['a.b'], 'foo', msg='argument with compound key should overwrite existing value')

    def test_config_from_file_argument(self):
        args = argv_to_dict(['script.py', '-a'])
        cfg = Config.load(StringIO('{}'), file_type='json').update_from_arguments(args)
        self.assertEqual(cfg['a'], True, msg='argument without parameters should be True in Config')

    def test_config_from_file_argument_override(self):
        args = argv_to_dict(['script.py', '-a'])
        cfg = Config.load(StringIO('{"a": 1}'), file_type='json').update_from_arguments(args)
        self.assertIsInstance(cfg['a'], int, msg='argument gets cast to type (int) of existing key')
        self.assertEqual(cfg['a'], True, msg='cast argument without parameters should equal True (1) in Config')
        cfg = Config.load(StringIO('{"a": "1"}'), file_type='json').update_from_arguments(args)
        self.assertIsInstance(cfg['a'], str, msg='argument gets cast to type (str) of existing key')
        self.assertEqual(cfg['a'], "True", msg='cast argument without parameters should equal "True" in Config')
