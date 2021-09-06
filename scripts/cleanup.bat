@echo off
REM change working directory to project root
cd %~dp0\..
REM remove folders and files created by build and deploy scripts
echo Removing 'dist', if it exists...
rmdir dist /s /q
echo Removing 'sdist', if it exists...
rmdir sdist /s /q
echo Removing 'build', if it exists...
rmdir build /s /q
echo Removing any '.egg-info' folders, if they exist...
for /f %%i in ('dir /a:d /s /b *.egg-info') do rmdir /s /q "%%i"
echo Removing any '__pycache__' folders, if they exist...
for /f %%i in ('dir /a:d /s /b __pycache__') do rmdir /s /q "%%i"