@echo off
REM change working directory to project root
cd %~dp0\..
REM run tests, only continue if tests succeeded
call scripts/run_tests.bat
if errorlevel 1 goto tests_failed
REM cleanup, build and deploy
call scripts/cleanup.bat
python setup.py sdist
pip install twine
if "%~1"=="no_test" (
  echo `no_test` provided, uploading to the real index PyPI https://pypi.org/
  twine upload dist/*
) else (
  echo `no_test` not provided, uploading to test index Test PyPI https://test.pypi.org/
  twine upload --repository testpypi dist/*
)
exit /b

:tests_failed
echo Some tests failed, please ensure no tests fail before trying to deploy. (and don't forget to commit and push first)
