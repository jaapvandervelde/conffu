@echo off
REM this assumes conffu is installed and Python is on the path, create an according virtual environment if needed

set PYTHONPATH=..

set y=5.0
set ec_x=Hello
set ec_y=10.0
set ec_{root}=%TEMP%

python env_cfg.py -x Hi
python env_cfg.py -evp ec_
python env_cfg.py -evp ec_ -cfg env_cfg.json
python env_cfg.py -cfg env_cfg.json
