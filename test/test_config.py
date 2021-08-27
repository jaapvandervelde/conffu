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

    def test_globals_list_config(self):
        cfg = DictConfig({'_globals': {'x': 1}, 'a': {'b': '{x}'}, 'c': [{'d': '{x}'}]})
        cfg_a = cfg['a']
        self.assertFalse('_globals' in cfg_a, msg='globals should be hidden for extracted child')
        self.assertEqual('1', cfg_a['b'], msg='globals should be propagated to Config child')
        cfg_list = cfg['c']
        self.assertEqual('1', cfg_list[0]['d'], msg='globals should be propagated to Config children in lists')

    def test_globals_noglobals(self):
        cfg = DictConfig({'_globals': {'x': 1}, 'test': '1={x}', 'escaped': '1={{x}}'}, no_globals=True)
        self.assertEqual('1={x}', cfg['test'], msg='noglobals, globals should not be replaced')
        self.assertEqual('1={{x}}', cfg['escaped'], msg='noglobals, escaped braces should not be unescaped')
        self.assertTrue('_globals' in cfg, msg='noglobals, globals should be visible')

    def test_globals_as_config(self):
        cfg = Config({'_globals': {'x': {'y': 1}}, 'a': {'b': 1}} )
        self.assertEqual(1, cfg.globals.x.y, msg='globals function as a config')
        a = cfg.a
        self.assertEqual(1, a.globals.x.y, msg='globals function as a config on a copy')
        self.assertEqual({'y': 1}, a.globals.x, msg='globals compare as a dict')

    def test_globals_assigned_dict(self):
        cfg_a = Config({'_globals': {'x': 1}, 'a': '{x}'})
        cfg_a['b'] = {'c': '{x}'}
        self.assertIsInstance(cfg_a.b, Config, 'type of parent is propagated to newly assigned dict')
        self.assertEqual('1', cfg_a.b.c, msg='newly assigned dicts inherit globals as config')

    def test_shared_globals(self):
        cfg_a = Config({'_globals': {'x': 1}, 'a': '{x}', 'b': {'c': '{x}'}})
        cfg_a.b.globals.x = 2
        self.assertEqual('2', cfg_a.a, msg='globals changes are indeed global and propagate')

    def test_globals_transfer(self):
        cfg_a = Config({'_globals': {'x': 1}, 'a': '{x}'})
        cfg_b = Config({'_globals': {'x': 2}, 'b': '{x}'})
        cfg_a['c'] = cfg_b
        self.assertEqual('1', cfg_a.c.b, msg='globals are updated to new parent globals')

    def test_globals_parent_transfer(self):
        cfg_a = Config({'_globals': {'x': 1}, 'a': '{x}', 'd': '{y}'})
        cfg_b = Config({'_globals': {'x': 2, 'y': 3}, 'b': '{x}'})
        cfg_a['c'] = cfg_b
        self.assertEqual('3', cfg_a.d, msg='parent globals are updated with new values from assigned config')

    def test_shadow_attrs(self):
        cfg = Config()
        cfg.shadow_attrs = True
        cfg['a'] = 1
        cfg.a = 2
        cfg.b = 1
        cfg['b'] = 2
        self.assertEqual((2, 2, 2, 2), (cfg.a, cfg['a'], cfg.b, cfg['b']), msg='attributes can be shadowed')

    def test_key_error(self):
        cfg = DictConfig({'test': 1})
        with self.assertRaises(KeyError, msg='without no_key_error, reading non-existent keys raises an exception'):
            cfg['more'] = cfg['more']

    def test_no_key_error(self):
        cfg = DictConfig({'test': 1}, no_key_error=True)
        cfg['more'] = cfg['more']
        self.assertEqual(cfg['more'], None, 'with no_key_error, reading non-existent keys returns None')

        cfg = DictConfig({'test': 1}, no_key_error=False)
        with self.assertRaises(KeyError):
            __ = cfg['more']
        try:
            __ = cfg.get('more')
        except KeyError:
            self.fail('get never raises a KeyError')


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
        self.assertEqual(3, cfg.test_2, 'keys can be accessed as attributes if they are not shadowed')
        del cfg.test
        self.assertEqual(2, cfg.test, 'if no longer shadowed by an attribute, keys can be access as attribute')

    def test_update(self):
        cfg = Config({1: 'a'})
        cfg = cfg | Config({1: 'b', 2: 'c'})
        self.assertEqual(('b', 'c'), (cfg[1], cfg[2]), 'updated values are correct')
        self.assertIsInstance(cfg, Config, msg='update should not affect type')

        cfg = DictConfig({1: 'a'})
        cfg = cfg | Config({1: 'b', 2: 'c'})
        self.assertIsInstance(cfg, DictConfig, msg='update with different Config type should not affect type')

        cfg = cfg | {1: 'b', 2: 'c'}
        self.assertIsInstance(cfg, DictConfig, msg='update with dict should not affect type')

    def test_update_reverse(self):
        cfg = Config({1: 'a'})
        cfg = Config({1: 'b', 2: 'c'}) | cfg
        self.assertEqual(('a', 'c'), (cfg[1], cfg[2]), 'updated values are correct')
        self.assertIsInstance(cfg, Config, msg='update should not affect type')

        cfg = DictConfig({1: 'a'})
        cfg = Config({1: 'b', 2: 'c'}) | cfg
        self.assertIsInstance(cfg, DictConfig, msg='update with different Config type should not affect type')

        cfg = {1: 'b', 2: 'c'} | cfg
        self.assertIsInstance(cfg, DictConfig, msg='update with dict should not affect type')

    def test_file_exists_error(self):
        with self.assertRaises(FileExistsError, msg='non-existent file raises correct exception'):
            cfg = Config.from_file('nonexistent.json')

    def test_disable_globals(self):
        cfg = Config({'_globals': {'x': 1}, 'xs': ['{x}']})
        self.assertEqual('1', cfg.xs[0], 'using globals regularly')
        cfg.xs.append('test')
        self.assertEqual(1, len(cfg.xs), 'cannot add to list while using globals')
        cfg.disable_globals = True
        cfg.xs.append('test')
        self.assertEqual(2, len(cfg.xs), 'can add to list while not using globals')
        self.assertEqual('test', cfg.xs[1], 'correct value added while not using globals')
        cfg.disable_globals = False

    def test_disable_globals_direct(self):
        cfg = Config({'_globals': {'x': 1}, 'xs': ['{x}']})
        with cfg.direct as dcfg:
            dcfg.xs.append('test')
            self.assertEqual(2, len(dcfg.xs), 'can add to list while not using globals through direct')
            self.assertEqual('test', dcfg.xs[1], 'correct value added while not using globals through direct')
        self.assertFalse(cfg.disable_globals, 'still using globals outside context')

        cfg = Config({'_globals': {'x': 1}, 'xs': ['{x}']})
        with cfg.direct:
            cfg.xs.append('test')
            self.assertEqual(2, len(cfg.xs), 'can add to list while not using globals through direct (no as)')
            self.assertEqual('test', cfg.xs[1], 'correct value added while not using globals through direct (no as)')

    def test_disable_globals_direct_persist(self):
        cfg = Config({'_globals': {'x': 1}, 'xs': ['{x}']})
        cfg.disable_globals = True
        with cfg.direct as dcfg:
            dcfg.xs.append('test')
            self.assertEqual(2, len(dcfg.xs), 'can add to list while not using globals through direct')
            self.assertEqual('test', dcfg.xs[1], 'correct value added while not using globals through direct')
        self.assertTrue(cfg.disable_globals, 'still using globals outside context')

    def test_get(self):
        cfg = Config({'_globals':{'g': 2}, 'a': 1, 'b': '{g}', 'c': {'d': 3}})
        self.assertEqual(1, cfg.get('a'), 'get works as expected')
        self.assertEqual('2', cfg.get('b'), 'get also resolves globals')
        self.assertEqual(3, cfg.get('c.d'), 'get also resolves compound keys')

        self.assertEqual('x', cfg.get('d', 'x'), 'get returns default for non-existent keys')

        cfg = Config({'_globals':{'g': 2}, 'a': 1, 'b': '{g}', 'c': {'d': 3}}, no_key_error=True)
        self.assertEqual('x', cfg.get('d', 'x'), 'get returns default for non-existent keys')

    def test_get_as_type(self):
        cfg = Config({'a': True, 'b': 'True', 'c': 0, 'd': 10})
        self.assertEqual(True, cfg.get_as_type('a', bool), 'same type get just returns value')
        self.assertEqual(True, cfg.get_as_type('b', bool), 'string booleans are returned as boolean')
        self.assertEqual(False, cfg.get_as_type('c', bool), 'int booleans are returned as boolean')
        self.assertEqual(True, cfg.get_as_type('d', bool), 'non-false string values are always true')
        self.assertEqual(None, cfg.get_as_type('x', bool), 'non-existent values are still returned as None')

    def test_relaxed_compound(self):
        cfg = Config({'63.2%': '1'})
        self.assertEqual('1', cfg['63.2%'], 'key available as non-compound is accessed normally')

    def test_relaxed_compound_nested(self):
        cfg = Config({'63.2%': {'a': '1'}})
        self.assertEqual({'a': '1'}, cfg['63.2%'], 'dictionary set as value for non-compound with period')
        self.assertEqual('1', cfg['63.2%']['a'], 'key available as non-compound is accessed normally as index')

        cfg = Config({'a.b': {'c': '1'}})
        self.assertEqual('1', cfg['a.b'].c, 'key available as non-compound is accessed normally as attribute')

    def test_relaxed_compound_problematic(self):
        cfg = Config({
            'a.b': [1],
        })
        self.assertEqual([1], cfg['a.b'], 'test case from oversee [1]')

    def test_pop(self):
        cfg = Config({'_globals':{'g': 2}, 'a': 1, 'b': '{g}', 'c': {'d': 3}})
        self.assertEqual(1, cfg.pop('a'), 'pop works as expected')
        with self.assertRaises(KeyError, msg='after pop, key no longer present'):
            cfg['a'] = cfg['a']
        cfg = Config({'_globals':{'g': 2}, 'a': 1, 'b': '{g}', 'c': {'d': 3}})
        self.assertEqual('2', cfg.pop('b'), 'pop also resolves globals')
        with self.assertRaises(KeyError, msg='after pop, key no longer present'):
            cfg['b'] = cfg['b']
        cfg = Config({'_globals':{'g': 2}, 'a': 1, 'b': '{g}', 'c': {'d': 3}})
        self.assertEqual(3, cfg.pop('c.d'), 'pop also resolves compound keys')
        self.assertEqual({}, cfg.c, 'pop also resolves compound keys')
        with self.assertRaises(KeyError, msg='after pop, key no longer present'):
            cfg['c.d'] = cfg['c.d']

    def test_del(self):
        cfg = Config({'_globals':{'g': 2}, 'a': 1, 'b': 2, 'c': {'d': 3}, 'e': {'f': 4}})
        cfg.g = 2
        cfg['g'] = 2
        del cfg.a
        del cfg['b']
        del cfg.c.d
        del cfg['e.f']
        del cfg.g
        self.assertTrue('a' not in cfg, 'key removed as attribute')
        self.assertTrue('b' not in cfg, 'key removed as index')
        self.assertTrue('c' in cfg, 'parent remains for removed compound key')
        self.assertTrue('d' not in cfg.c, 'sub-key removed for compound key')
        self.assertTrue('e' in cfg, 'parent remains for removed compound key')
        self.assertTrue('f' not in cfg.e, 'sub-key removed for compound key')
        self.assertTrue('g' in cfg, 'key not removed, when attr existed (and removed)')
        del cfg.g
        self.assertTrue('g' not in cfg, 'key removed after attr no longer existed')

        cfg = Config()
        cfg.shadow_attrs = True
        cfg.a = 2
        cfg['a'] = 1
        del cfg.a
        self.assertTrue('a' not in cfg, 'key removed even if attr exists, when attrs are shadowed')

    def test_update_basic(self):
        cfg = Config({'a': 1, 'b': 2, 'c': 3})
        cfg.update({'b': 3, 'd': 4}, c=5, e=6)
        self.assertEqual(1, cfg.a, 'untouched keys not affected by update')
        self.assertEqual(3, cfg.b, 'duplicated keys updated by update')
        self.assertEqual(5, cfg.c, 'duplicated kwargs keys updated by update')
        self.assertEqual(4, cfg.d, 'new keys added by update')
        self.assertEqual(6, cfg.e, 'new kwargs keys added by update')

        cfg = Config({'a': 1})
        cfg.update()
        self.assertEqual(cfg, Config({'a': 1}), 'no change from update with no arguments')
        cfg.update(a=2, b=3)
        self.assertEqual(2, cfg.a, 'kwargs keys correctly updated by update without mapping')
        self.assertEqual(3, cfg.b, 'kwargs keys correctly added by update without mapping')

    def test_update_globals(self):
        cfg = Config({'_globals':{'g1': 1, 'g2': 2}, 'a': '{g1}', 'b': '{g2}', 'c': '{g3}'})
        cfg_update = Config({'_globals': {'g2': 3, 'g3': 4}, 'd': '{g1}{g2}{g3}'})
        cfg.update(cfg_update)
        self.assertEqual('1', cfg.a, 'untouched global for update with globals')
        self.assertEqual('3', cfg.b, 'updated global for update with globals')
        self.assertEqual('4', cfg.c, 'added global for update with globals')
        self.assertEqual('134', cfg.d, 'correct global substitutions for newly added keys after update with globals')


if __name__ == '__main__':
    unittest.main()
