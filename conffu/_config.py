from re import split, sub
from typing import DefaultDict, Dict, Union, TextIO, List, Any, Generator, Tuple, Iterable
from sys import argv
from os import getenv, name as os_name, environ as os_environ
if os_name == 'nt':
    from nt import environ as nt_environ
from io import StringIO, BytesIO
from collections import defaultdict
from pathlib import Path

__version__ = '2.1.10'
GLOBALS_KEY = '_globals'

if os_name == 'nt':
    SWITCH_CHARS = '-/'
else:
    SWITCH_CHARS = '-'


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
        if len(a) > 0 and a[0] in SWITCH_CHARS:
            if len(a) == 1:
                raise SyntaxError(f'Syntax error in argument: {a}')
            key = a[2:] if a[:2] == '--' else a[1:]
            key = key if key not in aliases else aliases[key]
            # ensure the key is created (for arguments without value)
            _ = result[key]
        else:
            result[key].append(a)
    return result


class _NoGlobalsProxy:
    """
    This class only serves to provide a context manager for a DictConfig, to allow access to it with 'disable_globals'
    """
    def __init__(self, cfg: 'DictConfig'):
        self._cfg = cfg
        self._saved_value = False

    def __enter__(self):
        self._saved_value, self._cfg.disable_globals = self._cfg.disable_globals, True
        return self._cfg

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cfg.disable_globals = self._saved_value


class DictConfig(dict):
    """
    A dictionary-based configuration class, supports reading configurations from json, updating them from the command
    line arguments and allows for access using compound keys ('key.key') and global variable substitution

    :param args: arguments to be passed to the dict constructor
    :param no_globals bool: if not set, the value of the GLOBALS_KEY item will be take to be a dict of globals
        replacement values and this dict will be hidden from the DictConfig content
    :param no_key_error bool: if set, the DictConfig will not throw exceptions for non-existent keys (but return None)
    :param skip_lists bool: (deprecated 2.1.2, use skip_iterables) if True, casting should not recurse into lists
    :param skip_iterables bool: if set, dictionaries inside iterables (lists, tuples, subtypes) won't be forced to
        match the type of self

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
    # aliases for arguments -cfg for .load() and -evp for .update_from_arguments()
    ARG_MAP = {
        'config': 'cfg', 'configuration': 'cfg',
        'environment_variable_prefix': 'evp', 'env_var_prefix': 'evp',
        'request_header': 'rh', 'header': 'rh'
    }

    def __init__(self, *args, no_globals: bool = False, no_key_error: bool = False, skip_lists: bool = False,
                 no_compound_keys: bool = False, skip_iterables: bool = False):
        """
        Constructor method
        """
        super(DictConfig, self).__init__(*args)
        self.no_compound_keys = no_compound_keys
        self.no_key_error = no_key_error
        if no_globals is None:
            self.globals = None
        elif no_globals:
            if isinstance(no_globals, dict):
                # any dict type will be cast to type of self, with default settings
                self.globals = self.__class__(no_globals)
            else:
                self.globals = None
        else:
            # globals as part of a config only work if they are in the config and are actually a dict (or a Config)
            if GLOBALS_KEY not in self or not isinstance(super(DictConfig, self).__getitem__(GLOBALS_KEY), dict):
                self.globals = None
            else:
                # cast _globals dict in self to self type
                self.globals = self.__class__(super(DictConfig, self).__getitem__(GLOBALS_KEY))
                del self[GLOBALS_KEY]
        self.disable_globals = False
        self.filename = None
        self.arguments = None
        self.env_var_prefix = None
        self.cfg_filename = None
        self.parameters = None
        self.from_arguments = []
        # this attribute is only for the benefit of the Config subclass, which exposes it as a property
        self._shadow_attrs = False
        # replace dicts in Config with equivalent Config
        self._dicts_to_config(self, skip_iterables=skip_lists or skip_iterables)

    @property
    def direct(self):
        return _NoGlobalsProxy(self)

    def _dict_cast(self, a_dict: dict, from_type: type, to_type: type, skip_iterables: bool = False) -> dict:
        """
        Replace every dictionary of type `from_type` in a_dict with a dictionary of `to_type` configured like self,
        and do so recursively if `to_type` is equal to `self.__class__`
        :param a_dict: a variable inheriting from dict, the contents of which need to be cast
        :param from_type: a dict type to look for (either dict, or the DictConfig descendent type of self, typically)
        :param to_type: a dict type to cast to (either dict, or the DictConfig descendent type of self, typically)
        :param skip_iterables: whether dict elements of lists, tuples, or subtypes should be similarly cast
        :return dict: the in-place modified a_dict is returned as well
        """
        for key in a_dict:
            if isinstance(a_dict[key], from_type):
                self._dict_cast(a_dict[key], from_type, to_type, skip_iterables)
                if to_type is self.__class__:
                    a_dict[key] = to_type(a_dict[key], no_globals=self.globals, no_key_error=self.no_key_error,
                                          no_compound_keys=self.no_compound_keys)
                else:
                    a_dict[key] = to_type(a_dict[key])
            elif not skip_iterables and (isinstance(a_dict[key], list) or isinstance(a_dict[key], tuple)):
                a_dict[key] = a_dict[key].__class__(
                    part if not isinstance(part, from_type)
                    else (
                        to_type(self._dict_cast(part, from_type, to_type, skip_iterables),
                                no_globals=self.globals, no_key_error=self.no_key_error,
                                no_compound_keys=self.no_compound_keys)
                        if to_type is self.__class__
                        else to_type(self._dict_cast(part, from_type, to_type, skip_iterables))
                    )
                    # don't accidentally replace globals at this time, as a_dict[key] will access __getitem__
                    for part in (a_dict._get_direct(key) if isinstance(a_dict, DictConfig) else a_dict[key])
                )
        return a_dict

    def _dicts_to_config(self, d: dict, skip_iterables=False) -> dict:
        """
        Convert dict values of d to the same type as self (some DictConfig)
        :param d: dict with values to convert
        :param skip_iterables: if True, _dict_cast should not recurse into iterables (lists, tuples, subtypes)
        :return: d will have been modified in-place, and is returned
        """
        return self._dict_cast(d, dict, self.__class__, skip_iterables)

    def _configs_to_dict(self, d: dict, skip_iterables=False) -> dict:
        """
        Convert values of d of the same type as self (some DictConfig) to dict
        :param d: dict with values to convert
        :param skip_iterables: if True, _dict_cast should not recurse into iterables (lists, tuples, subtypes)
        :return: d will have been modified in-place, and is returned
        """
        return self._dict_cast(d, self.__class__, dict, skip_iterables)

    @staticmethod
    def _split_key(key: Union[str, list]) -> list:
        """
        Splits a compound configuration key into its parts and returns a list of a all parts
        :param key: a compound key (with '.' as a separator)
        :return: list of key parts
        """
        if isinstance(key, str):
            # split over periods, except when they are preceded by a backslash
            return split(r'(?<!\\)\.', key)
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

    def __or__(self, other):
        if not isinstance(other, dict):
            return NotImplemented
        new = self.__class__(self)
        new._shadow_attrs = self._shadow_attrs
        new.update(other)
        return new

    def __ror__(self, other):
        if not isinstance(other, dict):
            return NotImplemented
        new = self.__class__(other)
        new._shadow_attrs = self._shadow_attrs
        new.update(self)
        return new

    def __ior__(self, other):
        self.__class__.update(self, other)
        return self

    def _get_direct(self, key: str) -> Any:
        """
        Retrieve the item with (simple only) key from self and without performing global substitutions
        :param key: a simple key, with no parts separated by periods
        :return any: the value located with the compound key
        :raises KeyError: if the key cannot be found (and self.no_key_error is True, None otherwise)
        """
        return dict.__getitem__(self, key)

    class _Globals(dict):
        """
        Helper class for _subst_globals(), re-wrapping missing keys in {}
        """
        def __missing__(self, key: Any) -> str:
            return '{' + key + '}'

    def _subst_globals(self, value: Any) -> Any:
        if self.globals is None or self.disable_globals:
            return value
        else:
            if isinstance(value, str):
                try:
                    return value.format_map(self._Globals(self.globals))
                except AttributeError:
                    return value
            elif isinstance(value, list) or isinstance(value, tuple):
                # noinspection PyArgumentList
                return value.__class__(self._subst_globals(v) for v in value)
            elif isinstance(value, dict):
                if isinstance(value, Config):
                    # return the config at this time, as it will perform replacements when needed (if needed)
                    return value
                else:
                    # noinspection PyArgumentList
                    return value.__class__({k: self._subst_globals(v) for k, v in value.items()})
            else:
                return value

    def subst_globals(self) -> 'DictConfig':
        """
        Substitutes all globals in values of the config and returns the result
        :return: DictConfig with substituted string values
        """
        return self._subst_globals(self)

    def __getitem__(self, key: str) -> Any:
        """
        Retrieve the item with (compound) key from self
        :param key: a compound key, with parts separated by periods
        :return any: the value located with the compound key
        :raises KeyError: if the key cannot be found (and self.no_key_error is True, None otherwise)
        """
        if self.no_compound_keys:
            return super(DictConfig, self).__getitem__(key)

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
            return self._subst_globals(super(DictConfig, self).__getitem__(keys[0]))

    def __setitem__(self, key: str, value: Any):
        """
        Set the item with (compound) key in self
        :param key: a compound key, with parts separated by periods
        :param value: the value to be set on the key
        :return: None
        """
        try:
            if self.no_compound_keys:
                return super(DictConfig, self).__setitem__(key, value)
        except AttributeError:
            pass

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
                try:
                    self[keys[:-1]].shadow_attrs = self._shadow_attrs
                except AttributeError:
                    pass

    def dict_copy(self, skip_lists: bool = False, with_globals: bool = True, skip_iterables: bool = False) -> dict:
        """
        Copy the DictConfig as a dict, recursively (turning nested DictConfig into dict as well)
        :param skip_lists: (deprecated 2.1.2, use skip_iterables) if set, dictionaries in lists will not be cast
        :param with_globals: if set, globals will be included under the '_globals' key
        :param skip_iterables: if set, dictionaries in lists will be ignored (not converted)
        :return: a dictionary copy of self
        """
        # constructs a dict copy
        result = dict(self)
        # recurse into the copy, replacing DictConfig with dict
        self._configs_to_dict(result, skip_iterables=skip_iterables or skip_lists)
        if with_globals:
            result[GLOBALS_KEY] = dict(self.globals) if self.globals is not None else {}
        return result

    def copy(self) -> 'DictConfig':
        """
        Override to dict.copy, which would always return a `dict`, instead returning a copy with the same type as `self`
        :return: a copy of self, of the same type
        """
        return self.__class__(self.dict_copy())

    @classmethod
    def _xml2cfg(cls, root, **kwargs):
        """
        Takes an lxml root element and recursively parses it into a dict, which is then used to construct an instance
        of `cls`.
        :param root: xml.etree.ElementTree.Element root element of XML document
        :param kwargs: parameters to pass on to the constructor of this class, with a dict with the XML contents
        :return: an instance of `cls`
        """
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
    def _cfg2xml(cls, item: Union[int, float, list, dict], tag: str, etree, cfg_globals=None, exclude=None):
        """
        Take a dict (typically an instance of `cls`) and construct an lxml Element tree
        :param item: dict (or one of
        :param tag: tag name for the root tag of the (sub)tree being constructed
        :param etree: the ElementTree being constructed
        :param cfg_globals: globals of the root DictConfig to add to the xml document
        :param exclude: keys to exclude from the root DictConfig
        :return: root xml.etree.ElementTree.Element of etree
        """
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
    def _file_from_url(cls, url: str, url_header: Union[dict, str]):
        """
        Obtain a file-like object with the contents loaded from a URL
        :param url: the URL to load
        :param url_header: key value pairs to send as a header
        :return: file-like object as returned by request.urlopen
        """
        # only import urllib when it is actually used
        from urllib import request
        from urllib.parse import urlparse
        req = request.Request(url)
        if isinstance(url_header, str):
            try:
                url_header = {
                    k: sub(r'\\(.)', r'\1', v)
                    for k, v in [split(r'(?<!\\)=', pair) for pair in split(r'(?<!\\)&', url_header)]
                }
            except ValueError:
                raise ValueError(f'Invalid header fields: {url_header}')
        for k, v in url_header.items():
            req.add_header(k, v)
        return request.urlopen(req), Path(urlparse(url).path).name

    @classmethod
    def load(cls, source: Union[TextIO, BytesIO, str, Path] = None, file_type: str = None,
             no_arguments: bool = False, require_file: bool = True, url_header: Union[dict, str] = None,
             load_kwargs: dict = None, cli_args: Union[Dict[str, list], list, bool] = None,
             **kwargs) -> 'DictConfig':
        """
        Factory method that loads a Config from file and initialises a new instance with the contents.
        Currently only supports .json and .pickle
        :param source: existing configuration filename, url, or open file pointer
        :param file_type: either a file extension ('json', etc.) or None (will use the suffix of `filename`)
        :param no_arguments: (deprecated 2.1.2, use cli_args)
        :param cli_args: cli_args to pass to parse_arguments() if source is None, unless cli_args is False
        :param require_file: whether a configuration file is required (otherwise command line args only is accepted)
        :param url_header: a dictionary containing key values pairs to pass to a url request as a header, or a string
            encoded as the -rh parameter, e.g. 'key=value&key=value\\=\\&more'
        :param load_kwargs: a dictionary containing keyword arguments to pass to the format-specific load method
        :param kwargs: additional keyword arguments passed to Config constructor
        :return: initialised DictConfig instance
        """
        cfg = None
        args = None
        if source is None:
            if no_arguments is not True and cli_args is not False:
                args = cls._parse_arguments(cli_args=cli_args)
                if 'cfg' in args:
                    source = args['cfg'][0]
        if source is None:
            if require_file:
                raise SyntaxError('from_file requires a file parameter or configuration should be passed on the cli')
            else:
                cfg = cls()
                filename = None
        else:
            # determine filename and whether a file needs to be opened
            open_file = False
            if isinstance(source, str) or isinstance(source, Path):
                source = str(source)
                try:
                    if Path(source).is_file():
                        filename = source
                        open_file = True
                    else:
                        raise OSError
                except OSError:
                    try:
                        # at this point, file is neither a handle nor a valid file name, try it as a URL
                        if url_header is None and cli_args is not False:
                            if args is None:
                                args = cls._parse_arguments(cli_args)
                            if 'rh' in args:
                                url_header = args['rh'][0]
                        source, filename = cls._file_from_url(source, url_header if url_header is not None else {})
                    except (IOError, ValueError):
                        # at this point, file is neither a handle, a valid file name nor a valid URL
                        raise FileExistsError(f'Config file "{source}" not found.')
            else:
                try:
                    filename = source.name
                except AttributeError:
                    filename = None

            # determine file type from name, if not specified
            if file_type is None:
                if filename is None:
                    raise SyntaxError('File without name requires file_type to be specified')
                file_type = Path(filename).suffix.lower()[1:]

            try:
                # open file if needed at this point
                if open_file:
                    if file_type in ['json', 'xml']:
                        source = open(filename, 'r')
                    elif file_type == 'pickle':
                        source = open(filename, 'rb')
                else:
                    # if file is either a file object opened with 'b', or not a descendent of StringIO, wrap it
                    if file_type in ['json', 'xml'] and (
                            (hasattr(source, 'mode') and source.mode == 'b') or not isinstance(source, StringIO)):
                        source = StringIO(source.read().decode())

                # based on file_type, obtain cfg from the file handle
                if load_kwargs is None:
                    load_kwargs = {}
                if file_type == 'json':
                    import json
                    cfg = cls(json.load(source, **load_kwargs), **kwargs)
                elif file_type == 'pickle':
                    import pickle
                    cfg = pickle.load(source, **load_kwargs)
                elif file_type == 'xml':
                    from lxml import etree
                    root = etree.parse(source, **load_kwargs).getroot()
                    cfg = cls._xml2cfg(root, **kwargs)
            finally:
                if open_file:
                    source.close()

        cfg.filename = filename

        return cfg

    @classmethod
    def from_file(cls, file: Union[TextIO, BytesIO, str, Path] = None, file_type: str = None,
                  no_arguments: bool = False, require_file: bool = True, url_kwargs: dict = None,
                  load_kwargs: dict = None, **kwargs) -> 'DictConfig':
        """
        Deprecated as of 2.1.0, use DictConfig.load()
        """
        return cls.load(file, file_type, no_arguments, require_file, url_kwargs, load_kwargs, **kwargs)

    def save(self, file: Union[TextIO, BytesIO, str, Path] = None, file_type: str = None, include_globals: bool = True,
             include_from_arguments: bool = True, **kwargs):
        """
        Save the config to a file of the specified type
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
            skip_iterables = 'skip_lists' in kwargs and kwargs['skip_lists']
            skip_iterables = skip_iterables or ('skip_iterables' in kwargs and kwargs['skip_iterables'])
            data = self._configs_to_dict(self.__class__(self), skip_iterables=skip_iterables)
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

    def _recursive_keys_tuples(self) -> Generator[Tuple[str, Tuple[str]], None, None]:
        for key, value in self.items():
            yield key, (key,)
            if isinstance(value, DictConfig):
                for compound_sub_key, sub_key in value._recursive_keys_tuples():
                    yield f'{key}.{".".join(sub_key)}', tuple([key, *sub_key])

    def recursive_keys(self) -> Dict[str, Tuple[str]]:
        """
        a generator that yields every key in the DictConfig as a dictionary of compound key: key as a tuple
        :return: Generator[str, None, bool] containing all valid keys for self
        """
        return dict(self._recursive_keys_tuples())

    @staticmethod
    def _case_safe(key: str, keys: Iterable[str]) -> str:
        """
        helper function used by .update_from_environment()
        :param key: a key to match case for
        :param keys: keys to match key to and return instead
        :return: either key, or a case-insensitive matching key from keys
        """
        # only on Windows, replace the key with a matching key ignoring case
        if os_name == 'nt':
            for k in keys:
                if k.lower() == key.lower():
                    return k
        return key

    @classmethod
    def _parse_arguments(cls, cli_args: Union[Dict[str, list], list] = None, aliases: Dict[str, str] = None):
        """
        helper function used by .parse_arguments()
        :param cli_args: as for .parse_arguments()
        :param aliases: as for .parse_arguments()
        :return: parsed arguments as a dict or the same type as cli_args
        """
        if isinstance(cli_args, dict):
            if isinstance(cli_args, defaultdict):
                # noinspection PyArgumentList
                return cli_args.__class__(
                    cli_args.default_factory,
                    {aliases[k] if aliases is not None and k in aliases else k: v for k, v in cli_args.items()})
            else:
                # noinspection PyArgumentList
                return cli_args.__class__(
                    {aliases[k] if aliases is not None and k in aliases else k: v for k, v in cli_args.items()})
        else:
            return argv_to_dict(cli_args if isinstance(cli_args, list) else argv,
                                cls.ARG_MAP if aliases is None else aliases | cls.ARG_MAP)

    def parse_arguments(self, cli_args: Union[Dict[str, list], list] = None, aliases: Dict[str, str] = None):
        """
        Parse command line arguments (or passed arguments) and determine environment variable prefix and configuration
        filename. Arguments parsed are *added* to previously parsed arguments. Set self.arguments to None for a reset.
        :param cli_args: a list formatted like sys.argv, or a dictionary like the result from argv_to_dict of arguments,
            if None, sys.argv is used
        :param aliases: a dictionary of aliases for switches, e.g. {'help': 'h'}
        :return: self
        """
        if self.arguments is None:
            self.arguments = {}

        self.arguments = self.arguments | self._parse_arguments(cli_args, aliases)

        # allow chaining
        return self

    def update_from_environment(self, env_vars: list = None, exclude_vars: List = None, env_var_prefix: str = None):
        """
        Update the Config with values from the system environment. If no specific `env_vars` are provided, any value
        in the Config 'shadowed' by an environment variable will get updated. Globals will be picked up from the
        environment if environment variable matches the global enclosed in braces (any prefix outside braces).
        :param env_vars: specific variables to update or add from the environment, or None for pre-defined and prefixed
        :param exclude_vars: variables that should not be updated (typically if env_vars is None)
        :param env_var_prefix: prefix expected in front of every environment variables, e.g. 'MYAPP_'
        :return: self
        """
        if exclude_vars is None:
            exclude_vars = []

        self.env_var_prefix = (
            env_var_prefix if env_var_prefix is not None else
            self.arguments['evp'][0] if self.arguments is not None and 'evp' in self.arguments else
            self.env_var_prefix if self.env_var_prefix is not None else
            ''
        )

        environment = {}

        recursive_keys = self.recursive_keys()

        if env_vars is None:
            # check for all existing keys for a matching value in the environment to add (and not excluded)
            for compound_key, key in recursive_keys.items():
                if (getenv(self.env_var_prefix + compound_key) is not None and
                        self._case_safe(compound_key, exclude_vars) not in exclude_vars):
                    environment[key] = getenv(self.env_var_prefix + compound_key)
            # add all correctly prefixed from the environment
            if self.env_var_prefix != '':
                env = nt_environ if os_name == 'nt' else os_environ
                for var_name in env:
                    if var_name.lower().startswith(self.env_var_prefix.lower()):
                        v = var_name[(len(self.env_var_prefix)):]
                        if v[0] == '{' and v[-1] == '}':
                            environment[('_globals', v[1:-1])] = getenv(var_name)
                            if self.globals is None:
                                self.globals = {}
                            self.globals[v[1:-1]] = None
                        else:
                            if v in recursive_keys:
                                environment[recursive_keys[v]] = getenv(var_name)
                            else:
                                environment[v] = getenv(var_name)
                                self[v] = None
            # add existing globals found in environment in braces (if not excluded)
            elif self.globals is not None:
                for key in self.globals:
                    if (getenv(f'{{{key}}}') is not None and
                            self._case_safe(key, exclude_vars) not in exclude_vars):
                        environment[('_globals', key)] = getenv(f'{{{key}}}')
                        if self.globals is None:
                            self.globals = {}
        else:
            # check if the given keys are in the environment (and not excluded)
            for key in env_vars:
                if key[0] == '{' and key[-1] == '}':
                    if (getenv(self.env_var_prefix + key) is not None and
                            self._case_safe(key, exclude_vars) not in exclude_vars):
                        environment[('_globals', key)] = getenv(self.env_var_prefix + key)
                        if self.globals is None:
                            self.globals = {}
                else:
                    key = self._case_safe(key, recursive_keys)
                    if (getenv(self.env_var_prefix + key) is not None and
                            self._case_safe(key, exclude_vars) not in exclude_vars):
                        if key in recursive_keys:
                            environment[recursive_keys[key]] = getenv(self.env_var_prefix + key)
                        else:
                            # if the key didn't exist yet, add it and create it on the object
                            environment[key] = getenv(self.env_var_prefix + key)
                            self[key] = None

        # perform update with constructed environment (not using compound keys, for simplicity)
        for keys, value in environment.items():
            if keys[0] == '_globals':
                d = self.globals
                if keys[-1] not in d:
                    continue
            else:
                d = self
                for key in keys[:-1]:
                    d = d[key]
            key = keys[-1]

            # for bool, check specific non-True values
            if isinstance(d[key], bool):
                d[keys[-1]] = value.lower() not in ['0', 'false']
            else:
                # for other types, cast to type of existing key, or str if None
                if d[key] is None:
                    t = str
                else:
                    t = type(d[key])
                try:
                    d[keys[-1]] = t(value)
                except ValueError:
                    raise SyntaxError(f'Cannot cast {value} to {t} from environment')

        # allow chaining
        return self

    def _set_value_from_args(self, k, v):
        """
        helper function used by .update_from_arguments()
        :param k: key for value to set
        :param v: value to set
        :return: None
        """
        # is k an existing key?
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
                    raise SyntaxError(f'Cannot cast {v} to {t} from arguments')
        else:
            # define new key
            self.from_arguments.append(k)
            self[k] = v

    def _set_globals_from_args(self, k, v):
        """
        helper function used by .update_from_arguments()
        :param k: key for value to set
        :param v: value to set
        :return: None
        """
        if self.globals is None:
            self.globals = {}
        # for bool, check specific non-True values
        if k in self.globals and isinstance(self.globals[k], bool):
            self.globals[k] = v.lower() not in ['0', 'false']
        else:
            # for other types, cast to type of existing key
            t = type(self.globals[k]) if k in self.globals else type(v)
            try:
                self.globals[k] = t(v)
            except ValueError:
                raise SyntaxError(f'Cannot cast {v} to {t} from arguments')

    def update_from_arguments(self, cli_args: Union[Dict[str, list], list] = None, aliases: Dict[str, str] = None):
        """
        Update the Config with values parsed from the command line arguments. Overwriting values will be cast to the
        same type as the overwritten value, all other values will remain str. Parameters with no value will be set to
        True. If the config was created with `.from_file()` and `parse_args` was not False, it will use the arguments
        available at the time.
        :param cli_args: passed directly to .parse_arguments() if not None
        :param aliases: passed directly to .parse_arguments() if cli_args is not None
        :return: self
        """
        # if parse_arguments hasn't been called yet, or if new argument are passed, call parse_arguments
        if cli_args is not None or self.arguments is None:
            self.parse_arguments(cli_args, aliases)

        for key, value in self.arguments.items():
            if not key:
                # first value of '' key is the name of the program
                self.parameters = value[1:]
            elif key not in ['evp', 'cfg', 'rh']:
                if (key[0], key[-1]) == ('{', '}'):
                    key = key[1:-1]
                    update = self._set_globals_from_args
                else:
                    update = self._set_value_from_args
                # unpack single value lists
                if len(value) == 1:
                    update(key, value[0])
                else:
                    if not value:
                        # set to True for empty value
                        update(key, True)
                    else:
                        # set as list for multi-value
                        update(key, value)

        # allow chaining
        return self

    def full_update(self,
                    env_vars: list = None, exclude_vars: List = None, env_var_prefix: str = None,
                    cli_args: Union[Dict[str, list], list] = None, aliases: Dict[str, str] = None):
        """
        Calls .parse_arguments(), .update_from_environment() and .update_from_arguments() with provided arguments,
        for convenience
        :param cli_args: as cli_args in .parse_arguments()
        :param aliases: as in .parse_arguments()
        :param env_vars: as in .update_from_environment()
        :param exclude_vars: as in .update_from_environment()
        :param env_var_prefix: as in .update_from_environment()
        :return: self
        """
        # default for parse_args is True, while default for args is None, map one default to the other
        return self\
            .parse_arguments(cli_args, aliases)\
            .update_from_environment(env_vars, exclude_vars, env_var_prefix)\
            .update_from_arguments()


class Config(DictConfig):
    """
    A DictConfig that allows read access to its items as attributes.

    :Example:

    >>> dc = Config({'foo': 'bar'})
    >>> print(dc.foo)
    'bar'
    >>> dc.foo = 'qux'
    >>> print(dc['foo'])
    'qux'
    """
    @property
    def shadow_attrs(self):
        return self._shadow_attrs

    @shadow_attrs.setter
    def shadow_attrs(self, value):
        self._shadow_attrs = value

    def __getattr__(self, attr):
        if attr in self:
            return self[attr]
        else:
            raise AttributeError(f'No attribute or key {attr} for {self.__class__}')

    def __setattr__(self, attr, value):
        # check if configuration items can shadow object attributes, not using hasattr, as it will call __getattr__
        if (attr in dir(self) or attr not in self) and (not hasattr(self, '_shadow_attrs') or not self._shadow_attrs):
            super(DictConfig, self).__setattr__(attr, value)
        else:
            self[attr] = value
