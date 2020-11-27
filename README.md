# Conf Fu

A configuration package that allows you to configure your Python scripts, through a combination of JSON configuration files and command line options, with a minimum of code.

## Install

Install the package:
```
pip install conffu
```

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

## License

This project is licensed under the MIT license. See [LICENSE.txt](https://github.com/jaapvandervelde/gohlkegrabber/blob/master/LICENSE.txt).


## Changelog

- 2.0.0<br>First publicly released version after a major rewrite.
