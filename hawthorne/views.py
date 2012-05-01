''' views
the dynamic routes..how fun
'''
import datetime
from functools import wraps

from flask import (render_template, request, flash, redirect, url_for, session
    , abort)
from flaskext.bcrypt import Bcrypt
from mongoengine import *

from hawthorne import app
bcrypt = Bcrypt(app)

from models import *
import utilities


''' decorators
'''
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            app.logger.warning(
                'someone tried to access %s, a login-only page' % request.url)
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def verification_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # check that someone is logged in
        if 'email' not in session:
            app.logger.warning(
                'someone tried to access %s, a login-only page' % request.url)
            return redirect(url_for('login'))
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


''' routes
'''
@app.route('/register', methods=['GET', 'POST'])
@require_not_logged_in
def register():
    ''' displays registration page
    sends confirmation email to registrant
    sends notification email to admin
    '''
    if request.method == 'GET':
        return render_template('register.html')

    elif request.method == 'POST':
        # check that passwords match
        if request.form['password'] != \
            request.form['retype_password']:
            flash('submitted passwords did not match', 'error')
            return redirect(url_for('register'))

        # check that user email is unique
        duplicates = User.objects(email=request.form['email'])
        if duplicates:
            flash('This email address has been registered already.'
                , 'error')
            return redirect(url_for('register'))

        # create the new user
        try:
            new_user = User(
                admin_rights = False
                , api_id = 'ID' + utilities.generate_random_string(32)
                , api_key = utilities.generate_random_string(34)
                , email = request.form['email']
                , email_confirmation_code = \
                    utilities.generate_random_string(34)
                , email_confirmed = False
                , last_login_time = datetime.datetime.utcnow()
                , name = request.form['name']
                , organization = request.form['organization']
                , password_hash = bcrypt.generate_password_hash(
                    request.form['password'])
                , registration_time = datetime.datetime.utcnow()
                , verified = False
                , verified_by = None)
            new_user.save() 
        except:
            app.logger.error('user registration failed for %s' % \
                request.form['email'])
            flash('There was an error in the form, sorry :/', 'error')
            return redirect(url_for('register'))
        
        # seek email confirmation
        utilities.send_confirmation_email(new_user)

        # log the user in  
        session['email'] = new_user.email
        session['admin_rights'] = new_user.admin_rights

        # redirect to a holding area
        return redirect(url_for('verification_status'))


@app.route('/confirm-email/<code>')
def confirm_email(code):
    ''' click this link to confirm your email
    '''
    user = User.objects(email_confirmation_code=code)
    if not user:
        return redirect(url_for('home'))
    # save their email confirmation status
    user = user[0]
    user.email_confirmed = True

    # log the user in (controversy!)
    user.last_login_time = datetime.datetime.utcnow()
    user.save()
    session['email'] = user.email

    # email an admin for verification
    utilities.send_admin_verification(user)
        
    # redirect to a holding area
    return redirect(url_for('verification_status'))


@app.route('/verification-status')
@login_required
def verification_status():
    ''' shows verification status
    '''
    user = User.objects(email=session['email'])[0]
    # if verified/confirmed, redirect to dash
    return render_template('verification_status.html', user=user)


@app.route('/login', methods=['GET', 'POST'])
@require_not_logged_in
def login():
    ''' displays standalone login page
    handles login requests
    '''
    if request.method == 'GET':
        return render_template('login.html')

    elif request.method == 'POST':
        # find the user by their email
        user = User.objects(email=request.form['email'])
        if not user:
            app.logger.info('%s tried to login but is not known' % \
                request.form['email'])
            flash('That\'s not a valid email address or password.'
                , 'error')
            return redirect(url_for('login'))
        
        user = user[0]
        # verify the password 
        if not bcrypt.check_password_hash(user.password_hash
            , request.form['password']):
            app.logger.info('%s used the wrong password to login' % \
                request.form['email'])
            flash('That\'s not a valid email address or password.'
                , 'error')
            return redirect(url_for('login'))

        # they've made it through the gauntlet, log them in
        app.logger.info('%s logged in' % request.form['email'])
        user.last_login_time = datetime.datetime.utcnow()
        user.save()
        session['email'] = request.form['email']
        session['admin_rights'] = user.admin_rights

        return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    ''' blow away the session
    redirect home
    '''
    if 'email' in session:
        app.logger.info('%s logged out' % session['email'])
        session.pop('email', None)
        session.pop('admin_rights', None)

        flash('adios!', 'info')
    return redirect(url_for('home'))


@app.route('/dashboard')
@verification_required
def dashboard():
    ''' show the dashboard
    '''
    return render_template('dashboard.html')


@app.route('/directory/', defaults={'internal_id': None})
@app.route('/directory/<internal_id>', methods=['GET', 'POST'])
@admin_required
def directory(internal_id):
    ''' show the users and their verification/confirmation status
    if there's an email included in the route, render that profile for editing
    '''
    if request.method == 'POST':
        users = User.objects(id=internal_id)
        if not users:
            abort(404)
        user = users[0]

        profile_form_type = request.form.get('profile_form_type', '')
        if profile_form_type == 'info':
            if user.name != request.form.get('name', ''):
                app.logger.info('%s edited the name of %s to %s' % (
                    session['email'], request.form['email']
                    , request.form.get('name', '')))
                user.name = request.form.get('name', '')

            if user.email != request.form.get('email', ''):
                app.logger.info('%s edited the email of %s to %s' % (
                    session['email'], request.form['email']
                    , request.form.get('email', '')))
                user.email = request.form.get('email', '')

            if user.organization != request.form.get('organization', ''):
                app.logger.info('%s edited the organization of %s to %s' % (
                    session['email'], request.form['email']
                    , request.form.get('organization', '')))
                user.organization = request.form.get('organization', '')

            if request.form['verification'] == 'verified':
                # check to see if the verification status has changed
                if not user.verified:
                    app.logger.info('%s verified %s' % (session['email']
                        , request.form['email']))
                    # send email to user that they've been verified
                    utilities.send_notification_of_verification(user
                        , request.form.get('email', ''))
                user.verified = True

            elif request.form['verification'] == 'unverified':
                if user.verified:
                    app.logger.info('%s unverified %s' % (session['email']
                        , request.form['email']))
                user.verified = False
           
            if request.form['admin'] == 'admin':
                if not user.admin_rights:
                    app.logger.info('%s gave admin privileges to %s' % (
                        session['email'], request.form['email']))
                user.admin_rights = True

            elif request.form['admin'] == 'normal':
                if user.admin_rights:
                    app.logger.info('%s removed admin privileges from %s' % (
                        session['email'], request.form['email']))
                user.admin_rights = False
        
        elif profile_form_type == 'account':
            # delete the user
            user.delete()
            app.logger.info('%s deleted %s' % (session['email']
                , request.form['email']))
            flash('user deleted', 'success')
            return redirect(url_for('directory'))
        
        else:
            # bad 'profile_form_type'
            abort(404)
       
        try:
            user.save()
            flash('changes saved successfully', 'success')
        except:
            app.logger.error('%s experienced an error saving info about %s' % (
                session['email'], request.form['email']))
            flash('error saving changes, sorry /:')
        
        return redirect(url_for('directory', internal_id=user.id))

    
    if request.method == 'GET':
        if internal_id:
            user = User.objects(id=internal_id)
            if not user:
                abort(404)
            user = user[0]
            return render_template('directory_edit.html'
                , user=user)
        
        # nobody in particular was specified; show em all
        users = User.objects()
        return render_template('directory.html', users=users)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    ''' viewing/editing ones own profile
    note that admins can view/edit any profile at /directory
    '''
    user = User.objects(email=session['email'])[0]

    if request.method == 'POST':
        profile_form_type = request.form.get('profile_form_type', '')
        if profile_form_type == 'info':
            user.name = request.form.get('name', '')
            user.organization = request.form.get('organization', '')
        
        elif profile_form_type == 'password':
            # check that the current password is correct
            if not bcrypt.check_password_hash(user.password_hash
                , request.form['current_password']):
                flash('incorrect password', 'error')
                return redirect(url_for('profile', edit='true'))

            # submitted passwords are the same?
            if request.form['new_password'] != request.form['verify_password']:
                flash('new passwords do not match', 'error')
                return redirect(url_for('profile', edit='true'))

            # looking good; update the password
            user.password_hash = bcrypt.generate_password_hash(
                request.form['new_password'])

        elif profile_form_type == 'account':
            # delete the user, wipe the session
            app.logger.info('%s deleted his account' % session['email'])
            user.delete()
            session.pop('email', None)
            session.pop('admin_rights', None)

            flash('account deleted successfully', 'success')
            return redirect(url_for('home'))
        
        else:
            # bad 'profile_form_type'
            abort(404)
       
        try:
            user.save()
            flash('changes saved successfully', 'success')
            return redirect(url_for('profile'))
        except:
            flash('error saving changes, sorry /:')
            return redirect(url_for('profile'))
   

    if request.method == 'GET':
        if request.args.get('edit', '') == 'true':
            return render_template('profile_edit.html', user=user)
        else:
            return render_template('profile.html', user=user)


@app.route('/forgot/', defaults={'code': None}, methods=['GET', 'POST'])
@app.route('/forgot/<code>', methods=['GET', 'POST'])
def forgot(code):
    ''' take input email address
    send password reset link
    '''
    if request.method == 'POST':
        if code:
            user = User.objects(forgot_password_code=code)
            if not user:
                abort(404)
            user = user[0]

            user.password_hash = bcrypt.generate_password_hash(
                request.form['password'])
            user.save()

            app.logger.info('%s changed his password' % user.email)
            flash('password successfully changed; you may now login'
                , 'success')
            return redirect(url_for('home'))


        user = User.objects(email=request.form['email'])
        if not user:
            app.logger.info(
                'password reset of %s attempted but that email is not known' % 
                request.form['email'])
            flash('email not found :/', 'error')
            return redirect(url_for('forgot'))
        
        user = user[0]
        user.forgot_password_code = utilities.generate_random_string(34)
        user.save()
        #user.reload()

        utilities.send_forgot_password_link(user)
        
        app.logger.info('%s requested a forgotten password code' % \
            request.form['email'])

        flash('We\'ve sent an email to %s with information on how to \
            reset your account\'s password.' % user.email)
        return redirect(url_for('home'))

    elif request.method == 'GET':
        if code:
            user = User.objects(forgot_password_code=code)
            if not user:
                app.logger.warning('someone tried a bad password reset code')
                abort(404)
            user = user[0]
            return render_template('forgot_password_create_new.html'
                , user=user)
        else:
            return render_template('forgot.html')


''' jinja filters
formatters of sorts
'''
@app.template_filter('_format_datetime')
def _format_datetime(dt, formatting='medium'):
    ''' jinja filter for displaying datetimes
    usage in the jinja template:
        publication date: {{ article.pub_date|_format_datetime('full') }}
    '''
    if formatting == 'full':
        return dt.strftime('%A %B %d, %Y at %H:%M:%S')
    if formatting == 'medium':
        return dt.strftime('%B %d, %Y at %H:%M:%S')
    if formatting == 'full-day':
        return dt.strftime('%A %B %d, %Y')
    if formatting == 'short-date-with-time':
        return dt.strftime('%m/%d/%y %H:%M:%S')
    if formatting == 'day-month-year':
        return dt.strftime('%B %d, %Y')
    if formatting == 'hours-minutes-seconds':
        return dt.strftime('%H:%M:%S')

@app.before_request
def csrf_protect():
    ''' CSRF protection via http://flask.pocoo.org/snippets/3/
    '''
    if request.method == 'POST':
        token = session.pop('_csrf_token', None)
        if not token or token != request.form.get('_csrf_token'):
            if not app.config['TESTING']:
                app.logger.error('bad CSRF token')
                abort(403)

def _generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = utilities.generate_random_string(24)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = _generate_csrf_token






''' static_views
some of the more vanilla routes
'''

@app.route('/')
def home():
    ''' home page, how fun
    '''
    return render_template('home.html')


@app.route('/about')
def about():
    ''' show the about page
    '''
    return render_template('about.html')


@app.route('/help')
def help():
    ''' show the help page
    '''
    return render_template('help.html')


@app.route('/demo')
def demo():
    ''' show the demo video
    '''
    return render_template('demo.html')


''' error pages
'''
@app.errorhandler(404)
def page_not_found(error):
    ''' replaces stock 404 page
    '''
    return render_template('error_404.html'), 404


@app.errorhandler(500)
def server_error(error):
    ''' replaces stock 500 page
    '''
    return render_template('error_500.html'), 500



''' initialization
'''
def initialize_database():
    ''' adds a default admin to the system based on your settings
    usage:
        $ . /path/to/venv/bin/activate
        $ cd /path/to/hawthorne
        $ python
        >> import hawthorne
        >> hawthorne.views.initialize_database()
        user bruce@wayneindustries created with specified password
    '''
    # initialize the mongoengine connection
    # repeated to ensure any config changes from testing are pulled in
    connect(app.config['MONGO_CONFIG']['db_name']
        , host=app.config['MONGO_CONFIG']['host']
        , port=int(app.config['MONGO_CONFIG']['port']))

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

    default_admin.save()
    print 'user %s created with specified password' % default_admin['email']
