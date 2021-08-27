@echo off
call script/run_tests.bat
if errorlevel 1 goto tests_failed
git add .
git commit -m %1
git push github
git push origin
call script/cleanup.bat
call script/build.bat
twine upload dist/*
call script/cleanup.bat
goto end

:tests_failed
echo Some tests failed, please ensure no tests fail before deploying.

:end
