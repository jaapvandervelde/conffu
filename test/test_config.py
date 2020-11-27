import unittest
from conffu import DictConfig


class TestConfig(unittest.TestCase):
    def test_init_basic(self):
        cfg = DictConfig({'test': 1, 'more': 'string'})
        self.assertIsInstance(cfg, DictConfig)
        self.assertEqual(cfg['test'], 1, msg='int value should match')
        self.assertEqual(cfg['more'], 'string', msg='int value should match')

    def test_init_nested(self):
        cfg = DictConfig({'test': 1, 'more': {'content': 'string'}})
        self.assertIsInstance(cfg['more'], DictConfig, msg='inner dicts should be converted to Config')
        self.assertEqual(cfg['more']['content'], 'string', msg='value in inner dict should match')

    def test_init_nested_list(self):
        cfg = DictConfig({'test': 1, 'more': [{'content': 'string'}]})
        self.assertIsInstance(cfg['more'][0], DictConfig, msg='inner dicts in lists should be converted to Config')
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
        self.assertEqual(cfg['more'], None, 'with no_key_error, reading non-existent keys returns a default')


if __name__ == '__main__':
    unittest.main()
