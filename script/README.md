This folder contains scripts for writing, building, installing and maintaining your package project. Add additional scripts here.

Ideally, provide both Windows and Linux variants of scripts you add.

- [build_whl.bat](scripts/build_whl.bat) and [build_whl.sh](scripts/build_whl.sh)<br/>Builds a Python Wheel (.whl), so you can distribute a package as a single binary file (note that it still contains the source).
- [cleanup.bat](scripts/cleanup.bat) and [cleanup.sh](scripts/cleanup.sh)<br/>Cleans up files created by the build and deploy scripts.
- [deploy_to_pypi.bat](scripts/deploy_to_pypi.bat) and [deploy_to_pypi.sh](scripts/deploy_to_pypi.sh)<br/>Run tests, build and deploy to (test) PyPI. Pass `no_test` to deploy to the real index, or omit to deploy to the test index.
- [run_tests.bat](scripts/run_tests.bat) and [run_tests.sh](scripts/run_tests.sh)<br/>Runs unit tests in the [test](test) folder.

Any of these scripts can be started from other folders as well e.g., from the project root: `./script/build_whl.sh colchian` - the scripts will change their working directory to be the project root.
