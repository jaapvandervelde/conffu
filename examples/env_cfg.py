from pprint import pprint
from conffu import Config

"""
This script showcases some simple ways of using the environment and CLI to drive conffu. 

The script is called from env_cfg.bat, which contains:

    set y=5.0
    set ec_x=Hello
    set ec_y=10.0
    set ec_{root}=%TEMP%

These environment variables will be picked up by the calls to the script below.

This run will ignore the environment, as there are no environment variables that match defined variables (no 'x'):

    python env_cfg.py -x Hi

This run will print `{'x': 'Hello', 'y': '10.0'}` as `x` and `y` are both defined in the environment with the provided
prefix `ec_`. A global called `root` will also be defined, but not printed as globals are not printed on a Config.

    python env_cfg.py -evp ec_

This run will load `env_cfg.json` prior to applying the environment, and as a result will also print `'dir'` but
substitute `root` with the system temp directory; also, `y` will be a float instead of a string, as the type from the
loaded config file is matched for pre-existing variables. 

    python env_cfg.py -evp ec_ -cfg env_cfg.json
    
The final run will load the configuration from file, but as no prefix is specified, `y` is matched with the 
environment. Also, there's no global predefined for `ec_{root}` to match, so `dir` is unmodified and the script
will print `{'dir': '{root}/subdir/subdir', 'y': 5.0}`  
    
    python env_cfg.py -cfg env_cfg.json

Note that a common risk, if you don't specify what variables to load from the environment, is that you may see values 
overwritten unexpectedly. For example, if `dir` in the .json file was named `path` instead, it would likely be 
overwritten with the system PATH in the last example. To avoid this, the code below should read something like:

    cfg = Config.load(require_file=False).full_update(env_vars=['y'])
    
Or alternatively, to avoid a `path` variable getting overwritten (ignoring or inviting other overrides):

    cfg = Config.load(require_file=False).full_update(exlude_vars=['path'])
"""

# require_file is set to False to allow for cases where there's no loadable .cfg on the command line
cfg = Config.load(require_file=False).full_update()

pprint(cfg.subst_globals())
