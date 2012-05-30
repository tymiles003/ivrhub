''' question_views
creating and editing questions
'''
import os

import boto
from boto.s3.key import Key as S3_Key
from flask import (render_template, request, flash, redirect, url_for, session
    , abort, escape)
from flaskext.uploads import (UploadSet, configure_uploads, UploadNotAllowed)

from decorators import *
from models import *
import utilities
from ivrhub import app

uploaded_data = UploadSet('data', extensions=('mp3'))
configure_uploads(app, uploaded_data)

question_route = '/organizations/<org_label>/forms/<form_label>/questions'
@app.route(question_route, defaults={'question_label': None})
@app.route(question_route + '/<question_label>', methods=['GET', 'POST'])
@verification_required
@csrf_protect
def questions(org_label, form_label, question_label):
    ''' show the questions for a given form
    if there's a label included in the route, render that question alone
    '''
    user = User.objects(email=session['email'])[0]
    
    # find the relevant organization
    orgs = Organization.objects(label=org_label)
    if not orgs:
        app.logger.error('%s tried to access an organization that does not \
            exist' % session['email'])
        flash('Organization "%s" not found, sorry!' % org_label, 'warning')
        return redirect(url_for('organizations'))
    org = orgs[0]

    # permission-check
    if org not in user.organizations and not user.admin_rights:
        app.logger.error('%s tried to access an organization but was denied \
            for want of admin rights' % session['email'])
        abort(404)
    
    forms = Form.objects(label=form_label, organization=org)
    if not forms:
        app.logger.error('%s tried to access a form that does not \
            exist' % session['email'])
        flash('Form "%s" does not exist, sorry!' % form_label
            , 'warning')
        return redirect(url_for('organizations', org_label=org_label))
    form = forms[0]

    if request.method == 'POST':
        if not question_label:
            abort(404)

        questions = Question.objects(label=question_label, form=form)
        if not questions:
            abort(404)
        question = questions[0]

        form_type = request.form.get('form_type', '')

        if form_type == 'info':
            name = request.form.get('name', '')
            question.name = name
            question.label = str(escape(name).replace(' ', '-')).lower()
            question.description = request.form.get('description', '')

        elif form_type == 'prompt':
            # save response type
            question.response_type = request.form.get('response_type', '')

            # edit the prompt
            prompt_type = request.form.get('specify_prompt_type', '')
            question.prompt_type = prompt_type
            
            # check if a file has already been attached to this question
            audio_file_exists = request.form.get('audio_file_exists', '')

            if prompt_type == 'text_prompt':
                question.text_prompt = \
                    request.form.get('text_prompt', '').strip()
                question.text_prompt_language = \
                    request.form.get('text_prompt_language', '')

            elif prompt_type == 'audio_file' and audio_file_exists != 'true':
                # store in local dir then move to S3 and save key
                audio_file = request.files.get('audio_file')
                if not audio_file:
                    flash('Please specify a file.', 'error')
                    return redirect(url_for('questions', org_label=org.label
                        , form_label=form.label, question_label=question.label
                        , edit='true'))
                try:
                    filename = uploaded_data.save(audio_file)
                    absolute_filename = uploaded_data.path(filename)
                except UploadNotAllowed:
                    flash('This file type is not allowed, sorry.', 'error')
                    return redirect(url_for('questions', org_label=org.label
                        , form_label=form.label, question_label=question.label
                        , edit='true'))
                
                else:
                    # send to S3
                    access_key = app.config['AWS']['access_key_id']
                    secret = app.config['AWS']['secret_access_key']
                    connection = boto.connect_s3(
                        aws_access_key_id=access_key
                        , aws_secret_access_key=secret)

                    bucket_name = 'ivrhub-prompts-%s' % \
                        app.config['AWS']['access_key_id']
                    # creates bucket if it doesn't already exist
                    bucket = connection.create_bucket(bucket_name.lower())

                    s3_key = S3_Key(bucket)
                    # twilio requires the .mp3 suffix
                    s3_key.key = '%s.mp3' % \
                        utilities.generate_random_string(24)
                    s3_key.set_contents_from_filename(absolute_filename)
                    s3_key.make_public()
                    # generate public url with a long expiry
                    s3_url = s3_key.generate_url(5*365*24*60*60
                        , query_auth=False)

                    # save the key and url
                    question.audio_filename = filename
                    question.s3_key = s3_key.key
                    question.s3_url = s3_url

                    # remove from local filesystem
                    os.unlink(absolute_filename)

            elif prompt_type == 'audio_url':
                question.audio_url = request.form.get('audio_url', '').strip()
                

        elif form_type == 'admin':
            # blow away the question itself
            name = question.name
            utilities.delete_question(question)
            app.logger.info('%s deleted %s' % (session['email'], name))
            flash('Question "%s" was deleted.' % name, 'success')
            return redirect(url_for('forms', org_label=org.label
                , form_label=form.label))
        
        else:
            # bad 'form_type'
            abort(404)
        
        try:
            question.save()
            flash('Changes to this question were saved successfully'
                , 'success')
        except:
            question.reload()
            app.logger.error('%s experienced an error saving info \
                about question "%s"' % (
                session['email'], request.form['name']))
            flash('Error saving changes, are the names unique?', 'error')
        
        return redirect(url_for('questions', org_label=org_label
            , form_label=form.label, question_label=question.label
            , edit='true'))
       
    
    if request.method == 'GET':
        if question_label:
            questions = Question.objects(label=question_label, form=form)
            if not questions:
                abort(404)
            question = questions[0]

            if request.args.get('edit', '') == 'true':
                return render_template('question_edit.html', question=question)
            else:
                return render_template('question.html', question=question)

        if request.args.get('create', '') == 'true':
            # create a new question
            try:
                question_name = 'qst-%s' % utilities.generate_random_string(6)
                new_question = Question(
                    label = question_name.lower()
                    , form = form
                    , name = question_name
                )
                new_question.save()
                
                # attach to form
                form.update(push__questions=new_question)


                app.logger.info('question created by %s' % session['email'])
                flash('Question created; please change the defaults', 
                    'success')
                # redirect to the editing screen
                return redirect(url_for('questions', org_label=org_label
                    , form_label=form.label, question_label=new_question.label
                    , edit='true'))
            except:
                app.logger.error('question creation failed for %s' % \
                    session['email'])
                flash('There was an error in the form, sorry :/', 'error')
                return redirect(url_for('forms', org_label=org_label
                    , form_label=form.label))
        
        # nobody in particular was specified; punt for now
        abort(404)
