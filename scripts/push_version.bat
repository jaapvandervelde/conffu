@echo off
REM change working directory to project root
cd %~dp0\..
call scripts/run_tests.bat
if errorlevel 1 goto tests_failed
python scripts/quality.py
if errorlevel 1 goto quality_failed
git add .
git commit -m "update %1
git push github
git push origin
git tag %1
git push github %1
git push origin %1
goto end

:tests_failed
echo Some tests failed, please ensure no tests fail before deploying.
exit /b

:quality_failed
echo Some critical quality check failed, please remedy before trying to deploy.
exit /b

:end
