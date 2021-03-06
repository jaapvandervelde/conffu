import unittest
from conffu import DictConfig, Config


class TestConfig(unittest.TestCase):
    def test_init_basic(self):
        cfg = DictConfig({'test': 1, 'more': 'string', 'number': 1.3, 'list': [1, 2]})
        self.assertEqual(1, cfg['test'], msg='int value should match')
        self.assertIsInstance(cfg['test'], int, msg='int value maintains int type')
        self.assertEqual('string', cfg['more'], msg='str value should match')
        self.assertIsInstance(cfg['more'], str, msg='str value maintains str type')
        self.assertEqual(1.3, cfg['number'], msg='float value should match')
        self.assertIsInstance(cfg['number'], float, msg='float value maintains float type')
        self.assertEqual([1, 2], cfg['list'], msg='list value should match')
        self.assertIsInstance(cfg['list'], list, msg='list value maintains list type')

    def test_init_nested(self):
        cfg = DictConfig({'test': 1, 'more': {'content': 'string'}})
        self.assertIsInstance(cfg['more'], DictConfig, msg='inner dicts should be converted to same DictConfig type')
        self.assertEqual('string', cfg['more']['content'], msg='value in inner dict should match')
        cfg = Config({'test': 1, 'more': {'content': 'string'}})
        self.assertIsInstance(cfg['more'], Config, msg='inner dicts should be converted to same Config type')
        self.assertEqual('string', cfg['more']['content'], msg='value in inner dict should match')

        class MyConfig(Config):
            pass

        cfg = MyConfig({'test': 1, 'more': {'content': 'string'}})
        self.assertIsInstance(cfg['more'], MyConfig, msg='inner dicts should be converted to same custom Config type')
        self.assertEqual('string', cfg['more']['content'], msg='value in inner dict should match')

    def test_init_nested_list(self):
        cfg = DictConfig({'test': 1, 'more': [{'content': 'string'}]})
        self.assertIsInstance(cfg['more'][0], DictConfig, msg='inner dicts in lists should be converted to Config')
        self.assertEqual('string', cfg['more'][0]['content'], msg='value in inner dict in list should match')
        cfg = Config({'test': 1, 'more': [{'content': 'string'}]})
        self.assertIsInstance(cfg['more'][0], Config, msg='inner dicts in lists should be converted to Config')
        self.assertEqual('string', cfg['more'][0]['content'], msg='value in inner dict in list should match')

        class MyConfig(Config):
            pass

        cfg = MyConfig({'test': 1, 'more': [{'content': 'string'}]})
        self.assertIsInstance(cfg['more'][0], MyConfig, msg='inner dicts in lists should be converted to Config')
        self.assertEqual('string', cfg['more'][0]['content'], msg='value in inner dict in list should match')

    def test_init_nested_skip_list(self):
        cfg = DictConfig({'test': 1, 'more': [{'content': 'string'}]}, skip_iterables=True)
        self.assertIsInstance(cfg['more'][0], dict, msg='inner dicts in skipped lists should be dict')
        self.assertEqual('string', cfg['more'][0]['content'], msg='value in inner dict in skipped list should match')

    def test_globals_basic(self):
        cfg = DictConfig({'_globals': {'x': 1}, 'test': '1={x}', 'escaped': '1={{x}}'})
        self.assertEqual('1=1', cfg['test'], msg='globals should be replaced')
        self.assertEqual('1={x}', cfg['escaped'], msg='escaped braces should be unescaped')
        self.assertFalse('_globals' in cfg, msg='globals should be hidden')

    def test_globals_partial(self):
        cfg = DictConfig({'_globals': {'x': 1}, 'missing_y': '1={x}{y}'})
        self.assertEqual('1=1{y}', cfg['missing_y'], msg='missing globals should be left un-replaced')

    def test_globals_nested(self):
        cfg = DictConfig({'_globals': {'x': 1}, 'test': {'value': '1={x}', 'escaped': '1={{x}}'}})
        self.assertEqual('1=1', cfg['test']['value'], msg='nested globals should be replaced')
        self.assertEqual('1={x}', cfg['test']['escaped'],  msg='nested escaped braces should be unescaped')
        self.assertFalse('_globals' in cfg, msg='globals should be hidden')

        nested = cfg['test']
        self.assertEqual(1, nested.globals['x'], msg='nested configuration should inherit globals')
        self.assertEqual('1=1', nested['value'], msg='nested globals should be replaced with inherited globals')

    def test_globals_list(self):
        cfg = DictConfig({'_globals': {'x': 1}, 'test': ['1={x}', '1={{x}}']})
        self.assertEqual('1=1', cfg['test'][0], msg='globals in lists should be replaced')
        self.assertEqual('1={x}', cfg['test'][1], msg='escaped braces in lists should be unescaped')
        self.assertFalse('_globals' in cfg, msg='globals should be hidden')

    def test_globals_noglobals(self):
        cfg = DictConfig({'_globals': {'x': 1}, 'test': '1={x}', 'escaped': '1={{x}}'}, no_globals=True)
        self.assertEqual('1={x}', cfg['test'], msg='noglobals, globals should not be replaced')
        self.assertEqual('1={{x}}', cfg['escaped'], msg='noglobals, escaped braces should not be unescaped')
        self.assertTrue('_globals' in cfg, msg='noglobals, globals should be visible')

    def test_key_error(self):
        cfg = DictConfig({'test': 1})
        with self.assertRaises(KeyError, msg='without no_key_error, reading non-existent keys raises an exception'):
            cfg['more'] = cfg['more']

    def test_no_key_error(self):
        cfg = DictConfig({'test': 1}, no_key_error=True)
        cfg['more'] = cfg['more']
        self.assertEqual(cfg['more'], None, 'with no_key_error, reading non-existent keys returns None')

    def test_split_keys(self):
        cfg = Config({'test': {'nested': 1}})
        self.assertEqual(1, cfg['test.nested'], 'compound keys work as index')
        cfg = Config({'test.dot': {'extra': 1}}, no_compound_keys=True)
        self.assertEqual(1, cfg['test.dot']['extra'], 'keys with periods work without compound keys')
        cfg = Config({'test.dot': {'extra..': 1}}, no_compound_keys=True)
        self.assertEqual(1, cfg['test.dot']['extra..'], 'keys with periods work without compound keys, on sub configs')
        cfg = Config({'test': {'nested': 1}}, no_compound_keys=True)
        with self.assertRaises(KeyError, msg='with no_compound_keys, compound keys raise an exception'):
            cfg['test.nested'] = cfg['test.nested']

    def test_compound_keys(self):
        cfg = Config({'test': {'nested': {'deeper': 1}, 'also_nested': {}}}, no_compound_keys=False)
        self.assertEqual({
                             'test': ('test',),
                             'test.nested': ('test', 'nested'),
                             'test.nested.deeper': ('test', 'nested', 'deeper'),
                             'test.also_nested': ('test', 'also_nested')
                         },
                         cfg.recursive_keys(),
                         'compound keys are generated in order, depth-first')
        cfg = Config({'test.test': 1}, no_compound_keys=True)
        self.assertEqual({
                             'test.test': ('test.test',)
                         },
                         cfg.recursive_keys(),
                         'compound keys are generated in order, depth-first')

    def test_copy(self):
        cfg = Config({'1': 2})
        cfg_copy = cfg.copy()
        self.assertIsInstance(cfg_copy, Config, '.copy maintains original type Config')
        cfg = DictConfig({'1': 2})
        cfg_copy = cfg.copy()
        self.assertIsInstance(cfg_copy, DictConfig)
        self.assertIsInstance(cfg_copy, DictConfig, '.copy maintains original type DictConfig')
        d_copy = cfg.dict_copy()
        self.assertNotIsInstance(d_copy, DictConfig, '.dict_copy returns dict type copy instead of DictConfig')
        cfg = DictConfig({'1': 2, '3': {4: 5}, '6': [{'7': 8}]})
        self.assertIsInstance(cfg['3'], DictConfig, 'dictionary value matches self value')
        self.assertIsInstance(cfg['6'][0], DictConfig, 'dictionary value in list matches self value')
        d_copy = cfg.dict_copy(with_globals=False)
        self.assertNotIsInstance(d_copy['3'], DictConfig, '.copy returns dict value types')
        self.assertEqual({'1': 2, '3': {4: 5}, '6': [{'7': 8}]}, d_copy)
        cfg = DictConfig({'_globals': {'a': 'b'}, '1': 2, '3': {4: 5}, '6': [{'7': 8}]})
        d_copy = cfg.dict_copy()
        self.assertEqual({'1': 2, '3': {4: 5}, '6': [{'7': 8}], '_globals': {'a': 'b'}}, d_copy,
                         'globals survive dict_copy')

    def test_attr(self):
        cfg = Config()
        cfg.test = 1
        cfg['test'] = 2
        self.assertEqual(1, cfg.test, 'attributes are preferred over keys')
        self.assertEqual(2, cfg['test'], 'keys with names like attributes still work')
        cfg['test_2'] = 3
        self.assertEqual(3, cfg.test_2, 'keys can be accessed as attributes if they do are not shadowed')
        del cfg.test
        self.assertEqual(2, cfg.test, 'if no longer shadowed by an attribute, keys can be access as attribute')


if __name__ == '__main__':
    unittest.main()
