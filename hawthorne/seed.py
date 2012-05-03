''' database initialization
'''
import datetime

from flaskext.bcrypt import Bcrypt
from mongoengine import *

from hawthorne import app
bcrypt = Bcrypt(app)
from models import *
import utilities

def seed():
    ''' adds a default admin to the system based on your settings
    usage:
        $ . /path/to/venv/bin/activate
        (venv)$ python
        >> import hawthorne
        >> hawthorne.views.seed()
        user bruce@wayneindustries created with specified password
    '''
    # initialize the mongoengine connection
    # repeated to ensure any config changes from testing are pulled in
    connect(app.config['MONGO_CONFIG']['db_name']
        , host=app.config['MONGO_CONFIG']['host']
        , port=int(app.config['MONGO_CONFIG']['port']))

    users = User.objects()
    if not users:
        app.logger.info('no users in the db, so we will create one')
        initial_user = app.config['INITIAL_USER']

        default_admin = User(
            admin_rights = True
            , api_id = 'ID' + utilities.generate_random_string(32)
            , api_key = utilities.generate_random_string(34)
            , email = initial_user['email']
            , email_confirmation_code = utilities.generate_random_string(34)
            , email_confirmed = False
            , last_login_time = datetime.datetime.utcnow()
            , name = initial_user['name']
            , organization = initial_user['organization']
            , password_hash = bcrypt.generate_password_hash(
                initial_user['password'])
            , registration_time = datetime.datetime.utcnow()
            , verified = True
        )
        try:
            default_admin.save()
            app.logger.info('user %s created with specified password' % \
                default_admin['email'])
        except:
            app.logger.error('user %s could not be saved; check for dupes' % \
                default_admin['email'])
    else:
        app.logger.info('not seeding db as there are already users present')

