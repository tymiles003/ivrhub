flask app skeleton backed by mongodb

### Requirements
first off, you'll need a locally-running mongodb instance

use virtualenv and pip

    $ virtualenv /path/to/venv
    $ pip install -r requirements.txt -E /path/to/venv

after cloning, pull in the dependencies:
    
    $ git submodule init
    $ git submodule update


### Go-time
setup a real config file outside of source control

    $ cp conf/hawthorne_settings_sample.py /path/to/real/settings.py              

edit that new config..then point an env var at it

    $ export HAWTHORNE_SETTINGS=/path/to/real/settings.py

activate your virtualenv and create the default admin

    $ ./path/to/venv/bin/activate
    (venv)$ python
    >> import hawthorne
    >> hawthorne.views.seed()

start up the server

    (venv)$ python run.py


### Go-time in production
we have some example config files for supervisord, gunicorn, nginx, and fabric -- check those out
