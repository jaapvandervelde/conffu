# Changelog

Changes to this package will be documented in this file.

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
  
