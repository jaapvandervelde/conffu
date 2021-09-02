@echo off
REM change working directory to project root
cd %~dp0\..
REM run unit tests in ./test folder
python -m unittest discover -s ./test -t .\test
