import unittest
from conffu import DictConfig, Config


class TestConfig(unittest.TestCase):
    def test_init_basic(self):
        cfg = DictConfig({'test': 1, 'more': 'string', 'number': 1.3})
        self.assertEqual(cfg['test'], 1, msg='int value should match')
        self.assertEqual(cfg['more'], 'string', msg='str value should match')
        self.assertEqual(cfg['number'], 1.3, msg='float value should match')

    def test_init_nested(self):
        cfg = DictConfig({'test': 1, 'more': {'content': 'string'}})
        self.assertNotIsInstance(cfg['more'], Config, msg='inner dicts should be converted to same DictConfig type')
        self.assertEqual(cfg['more']['content'], 'string', msg='value in inner dict should match')
        cfg = Config({'test': 1, 'more': {'content': 'string'}})
        self.assertIsInstance(cfg['more'], Config, msg='inner dicts should be converted to same Config type')
        self.assertEqual(cfg['more']['content'], 'string', msg='value in inner dict should match')

        class MyConfig(Config):
            pass

        cfg = MyConfig({'test': 1, 'more': {'content': 'string'}})
        self.assertIsInstance(cfg['more'], MyConfig, msg='inner dicts should be converted to same custom Config type')
        self.assertEqual(cfg['more']['content'], 'string', msg='value in inner dict should match')

    def test_init_nested_list(self):
        cfg = DictConfig({'test': 1, 'more': [{'content': 'string'}]})
        self.assertNotIsInstance(cfg['more'][0], Config, msg='inner dicts in lists should be converted to Config')
        self.assertEqual(cfg['more'][0]['content'], 'string', msg='value in inner dict in list should match')
        cfg = Config({'test': 1, 'more': [{'content': 'string'}]})
        self.assertIsInstance(cfg['more'][0], Config, msg='inner dicts in lists should be converted to Config')
        self.assertEqual(cfg['more'][0]['content'], 'string', msg='value in inner dict in list should match')

        class MyConfig(Config):
            pass

        cfg = MyConfig({'test': 1, 'more': [{'content': 'string'}]})
        self.assertIsInstance(cfg['more'][0], MyConfig, msg='inner dicts in lists should be converted to Config')
        self.assertEqual(cfg['more'][0]['content'], 'string', msg='value in inner dict in list should match')

    def test_init_nested_skip_list(self):
        cfg = DictConfig({'test': 1, 'more': [{'content': 'string'}]}, skip_lists=True)
        self.assertIsInstance(cfg['more'][0], dict, msg='inner dicts in skipped lists should be dict')
        self.assertEqual(cfg['more'][0]['content'], 'string', msg='value in inner dict in skipped list should match')

    def test_globals_basic(self):
        cfg = DictConfig({'_globals': {'x': 1}, 'test': '1={x}', 'escaped': '1={{x}}'})
        self.assertEqual(cfg['test'], '1=1', msg='globals should be replaced')
        self.assertEqual(cfg['escaped'], '1={x}', msg='escaped braces should be unescaped')
        self.assertFalse('_globals' in cfg, msg='globals should be hidden')

    def test_globals_nested(self):
        cfg = DictConfig({'_globals': {'x': 1}, 'test': {'value': '1={x}', 'escaped': '1={{x}}'}})
        self.assertEqual(cfg['test']['value'], '1=1', msg='nested globals should be replaced')
        self.assertEqual(cfg['test']['escaped'], '1={x}', msg='nested escaped braces should be unescaped')
        self.assertFalse('_globals' in cfg, msg='globals should be hidden')

        nested = cfg['test']
        self.assertEqual(nested.globals['x'], 1, msg='nested configuration should inherit globals')
        self.assertEqual(nested['value'], '1=1', msg='nested globals should be replaced with inherited globals')

    def test_globals_list(self):
        cfg = DictConfig({'_globals': {'x': 1}, 'test': ['1={x}', '1={{x}}']})
        self.assertEqual(cfg['test'][0], '1=1', msg='globals in lists should be replaced')
        self.assertEqual(cfg['test'][1], '1={x}', msg='escaped braces in lists should be unescaped')
        self.assertFalse('_globals' in cfg, msg='globals should be hidden')

    def test_globals_noglobals(self):
        cfg = DictConfig({'_globals': {'x': 1}, 'test': '1={x}', 'escaped': '1={{x}}'}, no_globals=True)
        self.assertEqual(cfg['test'], '1={x}', msg='noglobals, globals should not be replaced')
        self.assertEqual(cfg['escaped'], '1={{x}}', msg='noglobals, escaped braces should not be unescaped')
        self.assertTrue('_globals' in cfg, msg='noglobals, globals should be visible')

    def test_key_error(self):
        cfg = DictConfig({'test': 1})
        with self.assertRaises(KeyError, msg='without no_key_error, reading non-existent keys raises an exception'):
            cfg['more'] = cfg['more']

    def test_no_key_error(self):
        cfg = DictConfig({'test': 1}, no_key_error=True)
        cfg['more'] = cfg['more']
        self.assertEqual(cfg['more'], None, 'with no_key_error, reading non-existent keys returns None')


if __name__ == '__main__':
    unittest.main()
