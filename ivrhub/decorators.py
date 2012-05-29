''' decorators
'''
from functools import wraps

from flask import (flash, session, redirect, request, url_for, abort)
from mongoengine import *

from hawthorne import app
from models import *

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
