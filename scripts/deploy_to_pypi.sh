#!/usr/bin/env bash
# change working directory to project root
cd "$(dirname "$0")/.." || exit
# run tests, only continue if tests succeeded
./scripts/run_tests.sh
if [ $? -ne 0 ]
  then
    echo "Some tests failed, please ensure no tests fail before trying to deploy. (and don't forget to commit and push first)"
    exit 1
fi
# cleanup, build and deploy
./scripts/cleanup.sh
python3 setup.py sdist
pip3 install --upgrade pip
python3 -m pip install twine
if [ "$1" == "no_test" ]
  then
    echo "'no_test' provided, uploading to the real index PyPI https://pypi.org/"
    python3 -m twine upload dist/*
  else
    echo "'no_test' not provided, uploading to test index Test PyPI https://test.pypi.org/"
    python3 -m twine upload --repository testpypi dist/*
fi
