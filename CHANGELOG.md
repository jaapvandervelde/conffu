# Changelog

## To do

When next major version is released (3.x), these breaking changes will be applied:
 - remove deprecated `skip_lists` from all methods
 - remove deprecated `.from_file()`
 - remove deprecated `no_arguments` from `.load()`
 - make `Config.shadow_attrs = True` the default 

## [2.1.11] - 2021-05-26

### Added
  - support for `.get()`, `.pop()` (previously, these would ignore globals and compound keys)
  - support for `del` (previously this wouldn't work when trying to delete an attribute, or with compound keys)
  - support for `.update()` (propagating globals correctly, overriding globals with globals from the update config)

## [2.1.10] - 2021-05-19

### Fixes
  - Path allowed as type for `.save()` and `.load()` methods.

## [2.1.9] - 2021-05-17

### Added
  - For easier access to the `.disable_globals` attribute and to avoid turning it back on, a context manager is provided through DictConfig.direct, for example:
```python
cfg = Config({'_globals': {'x': 1}, 'xs': []})
with cfg.direct:
    xs.append(1)  # this works, even though it wouldn't due to globals otherwise (see Fixes)
```

### Fixes
  - When accessing a list or tuple in a Config, a copy is returned if the Config has globals defines, to ensure substitutions work, but as a result calling methods on the list or tuple would no longer modify the original. To be able to modify a Config element through its methods and properties, a `disable_globals` property has been added which is `False` by default, but while `True`, allows direct unmodified access. 

## [2.1.8] - 2021-05-14

### Fixes
  - Config would not correctly catch the error thrown by `urlopen()` when trying to open a non-existent file as a URL.
  - `from_file` and `load` would accept a Path, but did not state this in their signature, causing undue IDE warnings.
  - removed unused import statements for `inspect` and `typing`.
  - too narrow parameter type for `recursive_keys()` (`List` to `Iterable`)

## [2.1.7] - 2021-04-22

### Added
  - Attribute `shadow_attrs` can be set on a `Config` to change the behaviour where setting a new value on a configuration would create an object attribute instead. Setting `cfg.shadow_attrs = True` now causes the config to allow setting new values, but it prevents normal creation of new attributes on the object with `cfg.attr = value`. </br><b>Deprecation warning</b>: As this is the preferred behaviour, but breaks backward compatibility, it will only become the default with the next major version. Set the property explicitly, which won't break for future versions.

## [2.1.6] - 2021-04-20

### Fixed
  - Child Configs, when extracted, should inherited the parent's globals, even when in an iterable. Previously they would be pre-emptively replaced. 

## [2.1.5] - 2021-03-29

### Added
  - Support for `|` update operator, to avoid the result always being a dict - preserves type.

## [2.1.4] - 2021-03-10

### Fixes
  - test using `http.server` would call `request.urlopen` before the server had started on Linux
  - `/` was recognised as a switch character on Linux, but should only be so on Windows

## [2.1.3] - 2021-03-06

### Added
  - `url_header` parameter on `.load()`, to allow for passing header fields to URL load.
  - `-rh` (`--request_header`, `--header`) command line option added to pass `url_header` for `.load()` on the CL<br>Example: 
```none
    script.py -cfg http://localhost:8000/my.json -rh "cookie=key\=one\&two&other_key=value with spaces"
```

### Changed
  - [deprecated] changed `no_arguments` on `.load()` to `cli_args`, matching `.parse_arguments()` with allowed added value of `False`, to allow for the case where a developer needs to pass arguments to the `.load()` method instead of using the actual arguments passed on the command line. This makes `no_arguments` deprecated. 

## [2.1.2] - 2021-03-06

### Changed
  - [deprecated] renamed `skip_lists` to `skip_iterables` as it works for list, tuple and subtypes

### Fixes
  - issue with environment variable case
  - added missing documentation on methods
  - updated unit tests

## [2.1.1] - 2021-03-05

### Changed
  - setting an attribute on Config that matches a key in the configuration will set that configuration item instead, without shadowing attributes on the configuration object

## [2.1.0] - 2021-03-03

### Changed
  - centralised CLI parameter parsing, exposed as `.parse_arguments()`
  - [deprecated] renamed some core methods and parameters to reflect function (`from_file` is now `load` with `source`, etc.)

### Added
  - environment variables can now be added based on a prefix, without being predefined in the config
  - globals can now be defined as environment variables and arguments as well
  - added `.full_update()` method to combine update from environment and arguments (in that order)
  - `from_file` alias for `load` for backward compatibility, now deprecated and will be removed in 3.x

### Fixes
  - issue with environment variable case
  - incorrect nested global replacement in edge cases
  - `DictConfig.copy()` now returns a `DictConfig` instead of a `dict`

## [2.0.8] - 2021-02-22

### Added
  - .from_file() now also accepts a URL as the source location to load a configuration from

### Fixed
  - case-sensitivity of enviroment variables and lack of tests on Linux

## [2.0.7] - 2021-02-01

### Added
  - updating values in the configuration from the system environment, similar to arguments
  - avoid case-sensitivity when updating values from the environment
  - support compound name settings from the environment, regardless of how the Config is set up

### Fixed
  - misreporting tests (swapping expected and realised value)
  - changelog updates not complete, fixed history back to 2.0.5

### Known issues
  - environment values are treated case-sensitive, both on Windows and Linux, against the expectation on Windows 

## [2.0.6] - 2021-01-07

### Fixed
  - keys with periods would always be parsed as compound keys, added option to disable compound keys

## [2.0.5] - 2020-12-07

### Added
  - QoL scripts for developer

### Fixed
  - values with replacements strings would not get global replacements when required
  - globals would get replaced when loading lists in configuration files with replacement strings
  - more explicit testing of configuration loading and roundtrips
  - incomplete docstrings 

## [2.0.4] - 2020-11-27

### Changed
  - formatting of changelog
  - changelog moved to CHANGELOG.md

### Fixed
  - another bugfix `extras_require` for `lxml`

## [2.0.3] - 2020-11-27

### Changed
  - moved scripts to `script/`

### Fixed
  - fix requirements.txt for package project
 
## [2.0.2] - 2020-11-27

### Added
  - Passing `load_kwargs` and `kwargs` to pickle and XML load and save methods

### Changed
  - updated faulty reference to license document from other project (no change in license)
  - centralised version references, to avoid version mismatches

### Fixed
  - bugfix `extras_require` for `lxml`

### Removed
  - removed default `pretty_print=True` from XML save method, should be passed in `kwargs`
  
## [2.0.1] - 2020-11-27

### Fixed
  - Fixed pickle bug with sub-configs and added a test for the pickle round-trip.

 ## [2.0.0] - 2020-11-27

### Added
  - First publicly released version after a major rewrite.
  
