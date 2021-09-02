#!/usr/bin/env bash
# change working directory to project root
cd "$(dirname "$0")/.." || exit
# install wheel if it isn't already
python3 -m pip install wheel
# build wheel
python3 setup.py sdist bdist_wheel
echo "If build succeeds and tests well, wheel is available in `dist`"
