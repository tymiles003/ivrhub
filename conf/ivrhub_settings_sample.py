'''
ivrhub_settings_sample.py
the following settings are placeholders
copy this file somewhere secure, rename it, and point an env var to it:
    $ export IVRHUB_SETTINGS=/path/to/settings.py
you may also want to do this in your .bashrc or .zshrc
'''
import logging

# the Flask application's debug level; /must/ be False for production
DEBUG = True

# generate a secret key with os.urandom(24)
SECRET_KEY = 'keep it secret, keep it safe'

# local testing parameters
APP_IP = '127.0.0.1'
APP_PORT = 8000

# app name and URL root, used in emails
APP_NAME = 'IVRHub'
APP_ROOT = 'http://127.0.0.1:8000'

# a path to your logfile
LOG_FILE = '/tmp/ivrhub.log'
LOG_LEVEL = logging.DEBUG

# the expiration time of 'remembered' sessions
PERMANENT_SESSION_LIFETIME = 180*24*60*60


# info on your local mongo instance
MONGO_CONFIG = {
    'db_name': 'ivrhub'
    , 'host': 'localhost'
    , 'port': 27017
}


# add a google analytics account id if you'd like to track page interaction
GOOGLE_ANALYTICS_ID = 'UA-12345678-9'


# where uploaded audio files are stored before being sent to S3
UPLOADED_DATA_DEST = '/tmp'


# amazon web services credentials
# you must verify a sender and seek production access via AWS SES
AWS = {
    'access_key_id': 'AKzyxw987'
    , 'secret_access_key': 'lmnop456'
    , 'verified_sender': 'bruce@wayneindustries.com'
}


# this user is injected into the database as the first admin
# can be used to promote other 'real' users to admins
INITIAL_USER = {
    'email': 'peter@dailybugle.net'
    , 'name': 'Peter Parker'
    , 'organization': 'The Daily Bugle'
    , 'password': 'ven0msuck5'
}


# create a gmail account you can access for testing
TEST_USER = {
    'email': 'thebat@gmail.com'
    , 'name': 'Bruce Wayne'
    , 'organization': 'Wayne Industries'
    , 'password': 'c4p3d-crus4d3r'
}
