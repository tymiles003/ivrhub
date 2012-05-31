''' decorators
'''
import base64
from functools import wraps
import hashlib

from flask import (flash, session, redirect, request, url_for, abort)
from mongoengine import *

from hawthorne import app
from models import *
import utilities

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            app.logger.warning(
                'someone tried to access %s, a login-only page' % request.url)
            flash('please login first', 'info')
            return redirect(url_for('login', then=request.path))
        return f(*args, **kwargs)
    return decorated_function


def verification_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # check that someone is logged in
        if 'email' not in session:
            app.logger.warning(
                'someone tried to access %s, a login-only page' % request.url)
            flash('please login first', 'info')
            return redirect(url_for('login', then=request.path))
        # check verification
        user = User.objects(email=session['email'])[0]
        if not user.verified:
            app.logger.warning('%s tried to access %s, a verified-only page' \
                % (session['email'], request.url))
            return redirect(url_for('verification_status'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # check that someone is logged in
        if 'email' not in session:
            app.logger.warning(
                'someone tried to access %s, a login-only page' % request.url)
            return abort(404)
        # check admin status
        user = User.objects(email=session['email'])[0]
        if not user.admin_rights:
            app.logger.warning('%s tried to access %s, an admin-only page' % (
                session['email'], request.url))
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function


def require_not_logged_in(f):
    ''' redirect if user is logged in already
    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' in session:
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def csrf_protect(f):
    ''' CSRF protection
    from bobince's answer at http://stackoverflow.com/questions/2695153
    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            if not app.config['TESTING']:
                submitted_token = request.form.get('_csrf_token', '')
                [submitted_salt, submitted_csrf_hash] = \
                    submitted_token.split('-')
                
                # get the user for their API key
                user = User.objects(email=session['email'])[0]

                # hash the app's secret with these values
                m = hashlib.md5()
                target = submitted_salt + user.api_key + \
                    base64.b64encode(app.config['SECRET_KEY'])
                m.update(target)

                if submitted_csrf_hash != m.hexdigest():
                    app.logger.error('bad CSRF token')
                    abort(403)

        return f(*args, **kwargs)
    return decorated_function


def _generate_csrf_token():
    ''' create a signed token
    signature is made with app's secret and user api key
    signed tokens (rather than per-request tokens) work across tabs
    they also play more nicely with AJAX
    still vulnerable to an attack from a verified user with an API key
    '''
    # create a random value
    salt = utilities.generate_random_string(24)

    # get the user for their API key
    user = User.objects(email=session['email'])[0]

    # hash the app's secret with these values
    m = hashlib.md5()
    target = salt + user.api_key + base64.b64encode(app.config['SECRET_KEY'])
    m.update(target)

    # create a token by combining the salt and hash
    token = salt + '-' + m.hexdigest()

    return token


app.jinja_env.globals['csrf_token'] = _generate_csrf_token
