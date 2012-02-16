'''
hawthorne_settings_sample.py
the following settings are placeholders
copy this file somewhere secure, rename it, and point an env var to it:
    $ export HAWTHORNE_SETTINGS=/path/to/settings.py
you may also want to do this in your .bashrc or .zshrc
'''

# the Flask application's debug level; /must/ be False for production
DEBUG = True

# generate a secret key with os.urandom(24)
SECRET_KEY = 'keep it secret, keep it safe'

# local testing parameters
APP_IP = '127.0.0.1'
APP_PORT = 8000


# info on your local mongo instance
MONGO_CONFIG = {
    'db_name': 'hawthorne'
    , 'host': 'localhost'
    , 'port': 27017
}
