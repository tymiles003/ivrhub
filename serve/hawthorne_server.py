#!/usr/bin/env python
'''
hawthorne_server.py
data entry management
'''
import datetime
from functools import wraps
import os

import flask
from flaskext.bcrypt import Bcrypt
from mongoengine import *


app = flask.Flask(__name__)
app.config.from_envvar('HAWTHORNE_SETTINGS')
bcrypt = Bcrypt(app)

# initialize the mongoengine connection
connect(app.config['MONGO_CONFIG']['db_name']
    , host=app.config['MONGO_CONFIG']['host']
    , port=int(app.config['MONGO_CONFIG']['port']))


''' decorators
'''
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in flask.session:
            return flask.redirect(flask.url_for('login'
                , next=flask.request.url))
        return f(*args, **kwargs)
    return decorated_function


''' routes
'''
@app.route('/')
def home():
    return flask.render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
# redirect-if-logged-in decorator
def register():
    ''' displays registration page
    sends confirmation email to registrant
    sends notification email to admin
    '''
    if flask.request.method == 'GET':
        return flask.render_template('register.html')

    elif flask.request.method == 'POST':
        # validate
        # hash password
        # submit new user
        # send verification email to registrant
        # send notification email to admin
        # redirect to a holding area
        return flask.redirect(flask.url_for('awaiting_confirmation'))


@app.route('/confirm/<code>')
def confirm(code):
    ''' email verification link
    '''
    # look up code
    # verify user email
    # check to see if verified 
    return flask.redirect(flask.url_for('awaiting_confirmation'))


@app.route('/awaiting_confirmation')
# redirect-if-not-logged-in decorator
def awaiting_confirmation():
    ''' shows verification status
    '''
    # if verified/confirmed, redirect to dash
    return flask.render_template('awaiting_confirmation.html')


@app.route('/login', methods=['GET', 'POST'])
# redirect-if-logged-in decorator
def login():
    ''' displays standalone login page
    handles login requests
    '''
    if flask.request.method == 'GET':
        return flask.render_template('login.html')

    elif flask.request.method == 'POST':
        # find the user by their email
        user = User.objects(email=flask.request.form['email'])
        if not user:
            return flask.render_template('login.html'
                , error='That\'s not a valid email address or password.')
        
        user = user[0]
        # verify the password 
        if not bcrypt.check_password_hash(user.password_hash
            , flask.request.form['password']):
            return flask.render_template('login.html'
                , error='That\'s not a valid email address or password.')

        # they've made it through the gauntlet, log them in
        user.last_login_time = datetime.datetime.utcnow()
        user.save()
        flask.session['email'] = flask.request.form['email']

        destination = flask.request.args.get('next', None)
        print destination
        if destination:
            return flask.redirect(destination)
        return flask.redirect(flask.url_for('dashboard'))


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    ''' blow away the session
    redirect home
    '''
    flask.session.pop('email', None)

    return flask.redirect(flask.url_for('home'))


@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    ''' show the dashboard
    '''
    return flask.render_template('dashboard.html')


@app.route('/directory/<email>', methods=['GET'])
# admin-only decorator
def directory(email):
    ''' show the users and their verification/confirmation status
    if there's an included in the route, render that profile for editing
    '''
    return flask.render_template('directory.html')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    ''' viewing/editing ones own profile
    admins can view/edit at /directory
    '''
    return flask.render_template('profile.html')


@app.route('/forgot/', defaults={'code': None})
@app.route('/forgot/<code>')
# logged-in decorator
def forgot(code):
    ''' take input email address
    send password reset link
    '''
    return flask.render_template('forgot.html')


''' mongoengine classes
'''
class User(Document):
    ''' some are admins some are not
    '''
    admin_rights = BooleanField(required=True)
    api_id = StringField()
    api_key = StringField()
    email = EmailField(required=True, unique=True, max_length=254)
    email_confirmation_code = StringField(required=True)
    email_confirmed = BooleanField(required=True)
    last_login_time = DateTimeField(required=True)
    name = StringField()
    organization = StringField(required=True)
    password_hash = StringField(required=True)
    registration_time = DateTimeField(required=True)
    verified = BooleanField(required=True)
    verified_by = EmailField()


''' utility functions
'''
def _generate_random_string(length):
    ''' generating API IDs and keys
    '''
    # technique from: http://stackoverflow.com/questions/2898685
    return ''.join(
        map(lambda x: '0123456789abcdefghijklmnopqrstuvwxyz'[ord(x)%36]
        , os.urandom(length)))


''' initialization
'''
def init():
    ''' adds a default admin to the system
    usage:
        $ /path/to/virtualenv/bin/python
        >> from hawthorne_server import init
        >> init()
        user bruce@wayneindustries created with specified password
    '''
    initial_user = app.config['INITIAL_USER']

    #try:
    default_admin = User(
        admin_rights = True
        , api_id = 'ID' + _generate_random_string(32)
        , api_key = _generate_random_string(34)
        , email = initial_user['email']
        , email_confirmation_code = _generate_random_string(34)
        , email_confirmed = False
        , last_login_time = datetime.datetime.utcnow()
        , name = initial_user['name']
        , organization = initial_user['organization']
        , password_hash = bcrypt.generate_password_hash(
            initial_user['password'])
        , registration_time = datetime.datetime.utcnow()
        , verified = True
        , verified_by = initial_user['email'])

    default_admin.save()
    print 'user %s created with specified password' % default_admin['email']
    #except:
    #    print 'insertion failed; there may be a non-unique field'


if __name__ == '__main__':
    app.run(
        host=app.config['APP_IP']
        , port=app.config['APP_PORT']
    )
