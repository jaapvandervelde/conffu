@echo off
git add .
git commit -m %1
git push
call script/cleanup.bat
call script/build.bat
echo run: twine upload dist/*
