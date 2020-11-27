import re
from typing import DefaultDict, Dict, Union, TextIO, List, Any
from sys import argv
from collections import defaultdict
from pathlib import Path

__version__ = '2.0.3'
GLOBALS_KEY = '_globals'


def argv_to_dict(args: List[str], aliases: Dict[str, str] = None) -> DefaultDict[str, list]:
    """
    Parse list of arguments (like sys.argv) into a dictionary; the resulting dictionary is a mapping from arguments
    to their values, while the program name and unnamed parameters will be mapped (in order) under the empty key ''.
    :param args: a list of command line parameters like sys.argv
    :param aliases: a dictionary with mappings for alternative parameter names [alias, parameter], e.g. {'help': 'h'}
    :return: dictionary with a mapping of resulting arguments and their values

    :example:

    >>> argv_to_dict(['test.py', 'file.txt', '-x', 'y', '/z', '--help'])
    defaultdict(<class 'list'>, {'': ['test.py', 'file.txt'], 'x': ['y'], 'z': [], 'help': []})
    """
    key = ''
    if aliases is None:
        aliases = {}
    result = defaultdict(list)
    for a in args:
        # arguments are prefixed with -, -- or / - no distinction for long names, so --h or -help would be valid
        if a[0] in '-/':
            if len(a) == 1:
                raise SyntaxError(f'Syntax error in argument: {a}')
            key = a[2:] if a[:2] == '--' else a[1:]
            key = key if key not in aliases else aliases[key]
            # ensure the key is created (for arguments without value)
            _ = result[key]
        else:
            result[key].append(a)
    return result


class DictConfig(dict):
    """
    A dictionary-based configuration class, supports reading configurations from json, updating them from the command
    line arguments and allows for access using compound keys ('key.key') and global variable substitution

    :param args: arguments to be passed to the dict constructor
    :param no_globals bool: if not set, the value of the GLOBALS_KEY item will be take to be a dict of globals
        replacement values and this dict will be hidden from the DictConfig content
    :param no_key_error bool: if set, the DictConfig will not throw exceptions for non-existent keys (but return None)
    :param skip_lists bool: if set, dictionaries inside lists won't be converted to DictConfig

    :example

    >>> dc = DictConfig({'_globals': { 'path': 'c:/temp'}, 'file': '{path}/foo.txt', 'sub': {'val': 1}})
    >>> dc
    {'file': '{path}/foo.txt', 'sub': {'val': 1}}
    >>> dc['file']
    'c:/temp/foo.txt'
    >>> dc['sub.val']
    1
    >>> type(dc['sub'])
    <class 'configuration._configuration.DictConfig'>
    """
    class _Globals(dict):
        def __missing__(self, key):
            return '{' + key + '}'

    def _dict_cast(self, a_dict: dict, from_type: type, to_type: type, skip_lists: bool = False):
        """
        Replace every instance of from_type in a_dict with a to_type configured like self, recursively
        if to_type is self.__class__
        :param a_dict: a variable inheriting from dict
        :return:
        """
        for key in a_dict:
            if isinstance(a_dict[key], from_type):
                self._dict_cast(a_dict[key], from_type, to_type, skip_lists)
                if to_type is self.__class__:
                    a_dict[key] = to_type(a_dict[key], no_globals=self.globals, no_key_error=self.no_key_error)
                else:
                    a_dict[key] = to_type(a_dict[key])
            elif not skip_lists and isinstance(a_dict[key], list):
                a_dict[key] = [
                    part if not isinstance(part, from_type)
                    else (
                        to_type(self._dict_cast(part, from_type, to_type, skip_lists),
                                no_globals=self.globals, no_key_error=self.no_key_error)
                        if to_type is self.__class__
                        else to_type(self._dict_cast(part, from_type, to_type, skip_lists))
                    )
                    for part in a_dict[key]
                ]
        return a_dict

    def _dicts_to_config(self, d: dict, skip_lists=False):
        return self._dict_cast(d, dict, self.__class__, skip_lists)

    def _configs_to_dict(self, cfg, skip_lists=False):
        return self._dict_cast(cfg, self.__class__, dict, skip_lists)

    def __init__(self, *args, no_globals: bool = False, no_key_error: bool = False, skip_lists: bool = False):
        """
        Constructor method
        """
        super(DictConfig, self).__init__(*args)
        self.no_key_error = no_key_error
        if no_globals is None:
            self.globals = None
        elif no_globals:
            if isinstance(no_globals, dict):
                self.globals = no_globals
            else:
                self.globals = None
        else:
            # globals as part of a config only work if they are in the config and are actually a dict (or a Config)
            if GLOBALS_KEY not in self or not isinstance(super(DictConfig, self).__getitem__(GLOBALS_KEY), dict):
                self.globals = None
            else:
                self.globals = super(DictConfig, self).__getitem__(GLOBALS_KEY)
                del self[GLOBALS_KEY]
        self.filename = None
        self.arguments = None
        self.parameters = None
        self.from_arguments = []
        # replace dicts in Config with equivalent Config
        self._dicts_to_config(self, skip_lists=skip_lists)

    @staticmethod
    def _split_key(key):
        if isinstance(key, str):
            # split over periods, except when they are preceded by a backslash
            return re.split(r'(?<!\\)\.', key)
        elif isinstance(key, list):
            return key
        else:
            return [key]

    def __contains__(self, key: str) -> bool:
        """
        returns whether the compound key ('part', 'part.part', etc.) is nested within self
        :param key: a compound key, with parts separated by periods
        :return bool: whether key is to be found in this object (and its nested children)

        :example:
        >>> dc = DictConfig({'a': {'b': 1}})
        >>> 'a.b' in dc
        True
        """
        keys = self._split_key(key)

        if not super(DictConfig, self).__contains__(keys[0]):
            return False
        return (len(keys) == 1) or (keys[1:] in self[keys[0]])

    def __getitem__(self, key: str) -> Any:
        """
        Retrieve the item with (compound) key from self
        :param key: a compound key, with parts separated by periods
        :return any: the value located with the compound key
        :raises KeyError: if the key cannot be found (and self.no_key_error is True, None otherwise)
        """
        keys = self._split_key(key)

        if self.no_key_error and keys[0] not in self:
            return None
        if isinstance(super(DictConfig, self).__getitem__(keys[0]), dict):
            if len(keys) == 1:
                # return any dictionary as a the same class as self
                return super(DictConfig, self).__getitem__(keys[0])
            else:
                return super(DictConfig, self).__getitem__(keys[0])[keys[1:]]
        else:
            if len(keys) > 1:
                if self.no_key_error:
                    return None
                else:
                    raise KeyError(f'Multi-part key, but `{keys[0]}` is not a dictionary or Config.')
            value = super(DictConfig, self).__getitem__(keys[0])
            if not isinstance(value, str) or self.globals is None:
                return value
            else:
                try:
                    return value.format_map(self._Globals(self.globals))
                except AttributeError:
                    pass

    def __setitem__(self, key: str, value: Any):
        """
        Set the item with (compound) key in self
        :param key: a compound key, with parts separated by periods
        :param value: the value to be set on the key
        :return: None
        """
        keys = self._split_key(key)

        if len(keys) == 0:
            raise KeyError(f'Invalid key value {key}.')
        elif len(keys) == 1:
            super(DictConfig, self).__setitem__(keys[0], value)
        else:
            try:
                target = self[keys[:-1]]
                target[keys[-1]] = value
            except KeyError:
                self[keys[:-1]] = self.__class__({keys[-1]: value})

    def dict_copy(self, skip_lists: bool = False, with_globals: bool = True) -> dict:
        """
        Copy the DictConfig as a dict, recursively (turning nested DictConfig into dict as well)
        :param skip_lists: if set, dictionaries in lists will be ignored (not converted)
        :param with_globals: if set, globals will be included under the '_globals' key
        :return: a dictionary copy of self
        """
        # constructs a dict copy
        result = dict(self)
        # recurse into the copy, replacing DictConfig with dict
        self._configs_to_dict(result, skip_lists=skip_lists)
        if with_globals:
            result[GLOBALS_KEY] = dict(self.globals)
        return result

    @classmethod
    def _xml2cfg(cls, root, **kwargs):
        if not len(root):
            ct = root.attrib['_type'] if '_type' in root.attrib else 'str'
            if ct == 'int':
                return int(root.text)
            elif ct == 'float':
                return float(root.text)
            elif ct == 'str':
                return root.text
            else:
                raise SyntaxError(f'Unknown type {ct} in xml.')
        result = {}
        for child in root:
            if len(child):
                if child[0].tag == '_'+child.tag:
                    # list
                    result[child.tag] = [
                        cls._xml2cfg(list_elem)
                        for list_elem in child if list_elem.tag == '_'+child.tag
                    ]
                else:
                    # dict
                    result[child.tag] = cls._xml2cfg(child)
            else:
                result[child.tag] = cls._xml2cfg(child)
        return cls(result, **kwargs)

    @classmethod
    def _cfg2xml(cls, item, tag, etree, cfg_globals=None, exclude=None):
        node = etree.Element(tag)
        if isinstance(item, int):
            node.attrib['_type'] = 'int'
            node.text = str(item)
        elif isinstance(item, float):
            node.attrib['_type'] = 'float'
            node.text = str(item)
        elif isinstance(item, list):
            for x in item:
                node.append(cls._cfg2xml(x, '_'+tag, etree))
        elif isinstance(item, dict):
            if cfg_globals is not None:
                node.append(cls._cfg2xml(cfg_globals, '_globals', etree))
            if exclude is None:
                exclude = []
            for tag, item in item.items():
                if tag not in exclude:
                    node.append(cls._cfg2xml(item, tag, etree))
        else:
            node.text = str(item)
        return node

    @classmethod
    def from_file(cls, file: Union[TextIO, str] = None, file_type: str = None,
                  parse_args: bool = True, require_file: bool = True, load_kwargs: dict = None, **kwargs):
        """
        Factory method that loads a Config from file and initialises a new instance with the contents.
        Currently only supports .json and .pickle
        :param file: existing configuration filename (or open file pointer)
        :param file_type: either a file extension ('json', etc.) or None (to use the suffix of `filename`)
        :param parse_args: whether to parse command line arguments to override 'cfg', list of args to override
        :param require_file: whether a configuration file is required (otherwise command line args only is accepted)
        :param load_kwargs: a dictionary containing keyword arguments to pass to the load method for the format
        :param kwargs: additional keyword arguments passed to Config constructor
        :return: initialised DictConfig instance
        """
        cfg = None
        if parse_args:
            mapping = {'config': 'cfg', 'configuration': 'cfg'}
            args = argv_to_dict(parse_args if isinstance(parse_args, list) else argv, mapping)
            if 'cfg' in args:
                file = args['cfg'][0]
        else:
            args = None
        if file is None:
            if require_file:
                raise SyntaxError('from_file requires a file parameter or configuration should be passed on the cli')
            else:
                cfg = cls()
                filename = None
        else:
            if isinstance(file, str) or isinstance(file, Path):
                file = str(file)
                if not Path(file).is_file():
                    raise FileExistsError(f'Config file {file} not found.')
                filename = file
            else:
                try:
                    filename = file.name
                except AttributeError:
                    filename = None
            if file_type is None:
                if filename is None:
                    raise SyntaxError('File without name requires file_type to be specified')
                file_type = Path(filename).suffix.lower()[1:]
            if load_kwargs is None:
                load_kwargs = {}
            if file_type == 'json':
                import json
                if isinstance(file, str):
                    with open(filename, 'r') as f:
                        cfg = cls(json.load(f, **load_kwargs), **kwargs)
                else:
                    cfg = cls(json.load(file, **load_kwargs), **kwargs)
            elif file_type == 'pickle':
                import pickle
                if isinstance(file, str):
                    with open(filename, 'rb') as f:
                        cfg = pickle.load(f, **load_kwargs)
                else:
                    cfg = pickle.load(file, **load_kwargs)
            elif file_type == 'xml':
                from lxml import etree
                root = etree.parse(file, **load_kwargs).getroot()
                cfg = cls._xml2cfg(root, **kwargs)

        cfg.filename = filename
        cfg.arguments = args

        return cfg

    def save(self, file: Union[TextIO, str] = None, file_type: str = None, include_globals: bool = True,
             include_from_arguments: bool = True, **kwargs):
        """
        Save the config to a file of specified type
        :param file: existing path to a file, if file exists, it will be overwritten (or file pointer open for writing)
        :param file_type: either a file extension ('json', etc.) or None (to use the suffix of `file`)
        :param include_globals: if True, globals (if any) will be written as part of the file, under GLOBAL_KEY
        :param include_from_arguments: if True, *new* values from arguments are added, *changed* values are always used
        :param kwargs: additional keyword arguments passed to underlying save methods
        :return: None
        """
        if file is None:
            file = self.filename
        if isinstance(file, str) or isinstance(file, Path):
            file = str(file)  # Path needs to be str as well
            filename = str(file)
        else:
            try:
                filename = file.name
            except AttributeError:
                filename = None

        if file_type is None:
            file_type = Path(filename).suffix.lower()[1:]

        if file_type == 'json':
            # create a dict-based copy of data
            data = self._configs_to_dict(self.__class__(self),
                                         skip_lists=False if 'skip_lists' not in kwargs else kwargs['skip_lists'])
            if include_globals:
                # force globals to be at the start of data
                data = {GLOBALS_KEY: self.globals, **data}

            import json
            if isinstance(file, str):
                with open(filename, 'w') as f:
                    json.dump(data, f, **kwargs)
            else:
                json.dump(data, file, **kwargs)
        elif file_type == 'pickle':
            import pickle
            if isinstance(file, str):
                with open(filename, 'wb') as f:
                    pickle.dump(self, f, **kwargs)
            else:
                pickle.dump(self, file, **kwargs)
        elif file_type == 'xml':
            from lxml import etree
            root = self._cfg2xml(self, 'config', etree, self.globals,
                                 [] if include_from_arguments else self.from_arguments)
            etree.ElementTree(root).write(file, encoding='utf-8', xml_declaration=True, **kwargs)

    def update_from_arguments(self, args: Union[Dict[str, list], list] = None, aliases: Dict[str, str] = None,
                              force_update=False):
        """
        Update the Config with values parsed from the command line arguments. Overwriting values will be cast to the
        same type as the overwritten value, all other values will remain str. Parameters with no value will be set to
        True.
        :param args: a dictionary of arguments, like the one returned by argv_to_dict, or a list like sys.argv
        :param aliases: a dictionary with mappings passed to argv_to_dict, if args is a dictionary
        :param force_update: whether to interpret args, even if self.arguments is not None
        :return: self
        """
        def set_value(k, v):
            # existing key?
            if k in self:
                # for bool, check specific non-True values
                if isinstance(self[k], bool):
                    self[k] = v.lower() not in ['0', 'false']
                else:
                    # for other types, cast to type of existing key
                    t = type(self[k])
                    try:
                        self[k] = t(v)
                    except ValueError:
                        raise SyntaxError(f'Cannot cast {v} to {t}')
            else:
                # define new key
                self.from_arguments.append(k)
                self[k] = v

        if args is None:
            args = argv
        if isinstance(args, list):
            if self.arguments is None or force_update:
                self.arguments = argv_to_dict(args, aliases)
        else:
            self.arguments = args

        for key, value in self.arguments.items():
            if not key:
                # first value of '' key is the name of the program
                self.parameters = value[1:]
            else:
                # unpack single value lists
                if len(value) == 1:
                    set_value(key, value[0])
                else:
                    if not value:
                        # set to True for empty value
                        set_value(key, True)
                    else:
                        # set as list for multi-value
                        set_value(key, value)
        return self


class Config(DictConfig):
    """
    A DictConfig that allows access to its items as attributes.

    :Example:

    >>> dc = Config({'foo': 'bar'})
    >>> print(dc.foo)
    'bar'
    """
    def __getattr__(self, attr):
        if attr in self:
            return self[attr]
        else:
            raise AttributeError(f'No attribute or key {attr} for {self.__class__}')
