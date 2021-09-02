@echo off
REM change working directory to project root
cd %~dp0\..
REM install wheel if it isn't already
pip install wheel
REM build wheel
python setup.py sdist bdist_wheel
echo If build succeeds and tests well, wheel is available in `dist`
