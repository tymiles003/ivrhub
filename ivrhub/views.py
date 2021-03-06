''' views
the dynamic routes..how fun
'''
import datetime

from flask import (render_template, request, flash, redirect, url_for, session
    , abort)
from flaskext.bcrypt import Bcrypt
from mongoengine import *

from ivrhub import app
bcrypt = Bcrypt(app)

# view controls
from decorators import *
# jinja filters and CSRF
from filters import *
# mongoengine models
from models import *
# db initialization
from seed import *
# util functions, mostly SES
import utilities
# boring routes
from vanilla_views import *
# other app views
from organization_views import *
from form_views import *
from question_views import *
from response_views import *
from incoming_views import *
from answer_views import *


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
                , email = request.form['email']
                , email_confirmation_code = \
                    utilities.generate_random_string(34)
                , email_confirmed = False
                , last_login_time = datetime.datetime.utcnow()
                , name = request.form['name']
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
        if request.form.getlist('remember') == 'on':
            session.permanent = True

        if request.args.get('then', ''):
            print request.args.get('then', '')
            return redirect(request.args.get('then', ''))

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


@app.route('/members/', defaults={'internal_id': None})
@app.route('/members/<internal_id>', methods=['GET', 'POST'])
@admin_required
@csrf_protect
def members(internal_id):
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
            
            if request.form['verification'] == 'verified':
                # check to see if the verification status has changed
                if not user.verified:
                    app.logger.info('%s verified %s' % (session['email']
                        , request.form['email']))
                    
                    # send email to user that they've been verified
                    utilities.send_notification_of_verification(user
                        , request.form.get('email', ''))
                    user.verified = True
                    
                    # create API credentials for the user
                    user.api_id = 'ID' + utilities.generate_random_string(32)
                    user.api_key = utilities.generate_random_string(34)

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
            # first pull out the user from the relevant orgs
            orgs = user.organizations
            for org in orgs:
                org.update(pull__users=user)
            
            # delete the user itself
            user_email = user.email
            user.delete()
            app.logger.info('%s deleted %s' % (session['email'], user_email))
            flash('user deleted', 'success')
            return redirect(url_for('members'))
        
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
        
        return redirect(url_for('members', internal_id=user.id))

    
    if request.method == 'GET':
        if internal_id:
            user = User.objects(id=internal_id)
            if not user:
                abort(404)
            user = user[0]
            return render_template('members_edit.html'
                , user=user)
        
        # nobody in particular was specified; show em all
        users = User.objects()
        return render_template('members.html', users=users)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
@csrf_protect
def profile():
    ''' viewing/editing ones own profile
    note that admins can view/edit any profile at /members
    '''
    user = User.objects(email=session['email'])[0]

    if request.method == 'POST':
        profile_form_type = request.form.get('profile_form_type', '')
        if profile_form_type == 'info':
            user.name = request.form.get('name', '')
        
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
@csrf_protect
@require_not_logged_in
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
