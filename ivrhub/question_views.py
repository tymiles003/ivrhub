''' question_views
creating and editing questions
'''
from flask import (render_template, request, flash, redirect, url_for, session
    , abort, escape)

from decorators import *
from models import *
import utilities
from ivrhub import app

question_route = '/organizations/<org_label>/forms/<form_label>/questions'
@app.route(question_route, defaults={'question_label': None})
@app.route(question_route + '/<question_label>', methods=['GET', 'POST'])
@verification_required
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
        return redirect(url_for('forms', org_label=org_label))
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
            app.logger.error('%s experienced an error saving info about \
                question "%s"' % (session['email'], request.form['name']))
            flash('Error saving changes, sorry /:')
        
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
