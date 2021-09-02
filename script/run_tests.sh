#!/usr/bin/env bash
# change working directory to project root
cd "$(dirname "$0")/.." || exit
# run unit tests in ./test folder
python3 -m unittest discover -s ./test -t ./test
