flask app skeleton backed by mongodb

### Requirements
use virtualenv and pip

    $ virtualenv /path/to/venv
    $ pip install -r requirements.txt -E /path/to/venv

after cloning, get the bootstrap and happy.js repos:
    
    $ git submodule init
    $ git submodule update


### Go-time
setup a real config file outside of your repo

    $ cp conf/hawthorne_settings_sample.py /path/to/real/settings.py              

edit that new config..then point an env var at it

    $ export HAWTHORNE_SETTINGS=/path/to/real/settings.py

activate your virtualenv and create the default admin

    $ ./path/to/venv/bin/activate
    (venv)$ cd serve
    (venv)$ python
    >> from hawthorne_server import init
    >> init()

start up the server

    (venv)$ python serve/hawthorne_server.py

one day that last command will use gunicorn or something..
