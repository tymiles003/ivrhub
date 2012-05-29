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

    $ cp conf/ivrhub_settings_sample.py /path/to/real/settings.py              

edit that new config..then point an env var at it

    $ export IVRHUB_SETTINGS=/path/to/real/settings.py

activate your virtualenv and create the default admin

    $ ./path/to/venv/bin/activate
    (venv)$ python
    >> import ivrhub 
    >> ivrhub.views.seed()

start up the server

    (venv)$ python run.py


### Go-time in production
we have some example config files for supervisord, gunicorn, nginx, and fabric -- check those out


### Bootstrapping a new server
 
 - install virtualenv and pip
 - copy over config files for supervisord, gunicorn, nginx and this app
 - make a dir for the config files and the log files
 - point the env var to the app config file and put this in your .zshrc
 - use fabric to install the app 
 - reload/reread/restart supervisord until it picks up the config file (annoyingly imprecise, I know..)
 - start the server and check with supervisorctl
 - edit the nginx config file at nginx.conf and the sites-availble dir (symlink to sites-enabled); restart nginx
 - seed the db from a shell
 - update your DNS 
