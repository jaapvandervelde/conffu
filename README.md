# Conf Fu

A configuration package that allows you to configure your Python scripts, through a combination of JSON configuration files and command line options, with a minimum of code.

## Install

Install the package:
```
pip install conffu
```
Note: on Linux, you may need to install `libffi-dev` and re-install Python if installation causes a 'No module named `_ctypes` error'. This is not specific to `conffu`, but any package requiring `_ctypes` in one of its dependencies.

If you want to be able to read/write XML configurations as well, there is a dependency on `lxml`, install using:
```
pip install conffu[xml]
```

## Example

With the package installed, try running this script:
```
from conffu import Config

cfg = Config({
    '_globals': {
        'temp': 'C:/Temp'
    },
    'temp_file': '{temp}/text.txt',
    'number': 3
})

print(f'The number is {cfg.number}')

cfg.save('example_config.json')
```

After running that, this also works:
```
from conffu import Config

cfg = Config.from_file('example_config.json')
print(f'The number is {cfg.number}')
```

Make a change and save this script as `example.py`:
```
from conffu import Config

cfg = Config.from_file('example_config.json').update_from_arguments()
print(f'The number is {cfg.number}')
```

Then try running it like this:
```
python example.py -number 7
``` 

There's many more options, check the documentation for more examples.

### Caveat

Note that `Config` allows you to do this:
```python
from conffu import Config

cfg = Config()
cfg['test'] = 1
print(cfg.test)  # prints 1
```
That is, you're allowed to access configuration keys as if they were attributes on the configuration. However, if you try to access a key that happens to also be an attribute on the object, you get the attribute. This has the advantage that the feature doesn't break how objects work in Python, but the disadvantage that you'll need to access keys that have the same name as object attributes using the dictionary syntax. For example:
```python
from conffu import Config

cfg = Config()
cfg.test = 1
cfg['test'] = 2
cfg.test = 3
cfg.['test'] = 4
print(cfg.test, cfg['test'])  # prints 3 4 instead of 4 4
```
If you don't like this behaviour, use the `DictConfig` class instead of `Config` - they are identical, except that the `DictConfig` does not have this behaviour and you always access keys like `cfg['test']`, or `cfg['key.subkey']`.

## License

This project is licensed under the MIT license. See [LICENSE.txt](https://gitlab.com/Jaap.vanderVelde/conffu/-/blob/master/LICENSE.txt).

## Changelog

See [CHANGELOG.md](https://gitlab.com/Jaap.vanderVelde/conffu/-/blob/master/CHANGELOG.md).
