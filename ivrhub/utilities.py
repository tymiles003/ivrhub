''' utility functions
'''
import os
import urlparse

import boto
from flask import (url_for)

from ivrhub import app
from models import *


def delete_response(response):
    ''' remove specified response
    also delete all relevant answers
    '''
    # first remove all answers
    answers = Answer.objects(response=response)
    for answer in answers:
        answer.delete()

    # blow away the response itself
    response.delete()


def delete_form(form):
    ''' delete specified form
    also delete all associated questions
    '''
    # delete all associated questions
    for question in form.questions:
        delete_question(question)

    # delete all associated responses
    responses = Response.objects(form=form)
    for response in responses:
        delete_response(response)

    form.delete()


def delete_question(question):
    ''' delete specified question
    also remove it from the associated form
    '''
    if question.s3_key:
        # connect to S3 and remove the file
        connection = boto.connect_s3(
            aws_access_key_id=app.config['AWS']['access_key_id']
            , aws_secret_access_key=app.config['AWS']['secret_access_key'])

        bucket_name = 'ivrhub-prompts-%s' % app.config['AWS']['access_key_id']
        bucket = connection.create_bucket(bucket_name.lower())
        bucket.delete_key(question.s3_key)
    
    # pull the question from the form
    form = question.form
    form.update(pull__questions = question)
    
    # blow away the question itself
    question.delete()


def generate_random_numeric_string(length):
    ''' generate string of random numbers
    '''
    return ''.join(map(lambda x: '0123456789'[ord(x)%10]
        , os.urandom(length)))


def generate_calling_code(length):
    ''' generate a random suitable calling code
    should be easy to type as an sms
    '''
    while(1):
        code = generate_random_numeric_string(length)
        forms = Form.objects(calling_code=code)
        if not forms:
            break
    return code


def generate_random_string(length):
    ''' generating API IDs and keys
    '''
    # technique from: http://stackoverflow.com/questions/2898685
    return ''.join(
        map(lambda x: '0123456789abcdefghijklmnopqrstuvwxyz'[ord(x)%36]
        , os.urandom(length)))

        
def send_forgot_password_link(user):
    ''' user has requested password reset link
    '''
    forgot_url = urlparse.urljoin(app.config['APP_ROOT']
        , url_for('forgot_password', code=user.forgot_password_code))

    body = '''
        Hello!  Someone has recently requested a password reset for %s.  
        If that was not you, please disregard this message.  
        
        If it was you, please click this link to choose a new password, thanks!
        
        %s
         ''' % (app.config['APP_NAME'], forgot_url)

    _send_email(user.email
        , 'Re: requested %s password reset' % app.config['APP_NAME']
        , body)
    

def send_notification_of_verification(user, email):
    ''' email a user that they've been verified by an admin and now have full
    access to the site
    '''
    if not email:
        app.logger.error('no verification email specified for %s.  \
            email on record is %s' % (user.name, user.email))
    else:
        body = '''
            Hello!  Your information has been verified by an administrator and
            you now have full access to %s.
            
            Just wanted to let you know, thanks!

            %s
            ''' % (app.config['APP_NAME'], app.config['APP_ROOT'])

        _send_email(user.email
            , 'you now have access to %s' % app.config['APP_NAME']
            , body)


def send_admin_verification(user):
    ''' email to an admin indicating that there a user needs verification
    '''
    members_url = urlparse.urljoin(app.config['APP_ROOT']
        , url_for('members', internal_id=user._id))

    body = '''
        Howdy!  Someone new has confirmed his or her email address and now 
        needs to be verified by an admin.  Here are the details:

        Name: %s
        Email: %s

        Click the following link to edit the verification status of this
        person.

        %s

        Thanks!
        ''' % (user.name, user.email, members_url)

    # send to the AWS verified sender
    # ..should probably use a manager's email instead
    _send_email( app.config['AWS']['verified_sender']
        , '%s | %s needs to be verified' % (app.config['APP_NAME'], user.name)
        , body)


def send_confirmation_email(user):
    ''' sends an email to a newly-registered user with a confirmation code
    '''
    confirmation_url = urlparse.urljoin(app.config['APP_ROOT']
        , url_for('confirm_email', code=user.email_confirmation_code))

    body = '''
        Hello, this email was recently used to sign up for an account with 
        %s.  If it was you that signed up for this account, please click
        the link below to confirm your email address.
        
        If you did not sign up for this account, please disregard this message.
        
        %s

        Thanks!
        ''' % (app.config['APP_NAME'], confirmation_url)

    _send_email( user.email
        , '%s email confirmation' % app.config['APP_NAME']
        , body)


def _send_email(recipient, subject, body):
    ''' send an email using SES from the config's verified sender
    '''
    connection = boto.connect_ses(
        aws_access_key_id=app.config['AWS']['access_key_id']
        , aws_secret_access_key=app.config['AWS']['secret_access_key'])

    result = connection.send_email(
        app.config['AWS']['verified_sender']
        , subject
        , body
        , [recipient])
    # need to catch errors in result
