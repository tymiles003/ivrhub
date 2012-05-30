''' decorators
'''
from functools import wraps

from flask import (flash, session, redirect, request, url_for, abort)
from mongoengine import *

from ivrhub import app
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
    ''' CSRF protection via http://flask.pocoo.org/snippets/3/
    using decorator rather than 'before_request' as twilio routes need to \
    skip csrf-check
    '''
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'POST':
            token = session.pop('_csrf_token', None)
            if not token or token != request.form.get('_csrf_token'):
                if not app.config['TESTING']:
                    app.logger.error('bad CSRF token')
                    abort(403)
        return f(*args, **kwargs)
    return decorated_function

def _generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = utilities.generate_random_string(24)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = _generate_csrf_token
