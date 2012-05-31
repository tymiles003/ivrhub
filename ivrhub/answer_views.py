''' answers_views
annotating answers
'''
from flask import (render_template, request, flash, redirect, url_for, session
    , abort)

from decorators import *
from models import *
from ivrhub import app


answer_route = '/organizations/<org_label>/forms/<form_label>/responses'
answer_route += '/<response_sid>/answers/<question_label>'
@app.route(answer_route, methods=['GET', 'POST'])
@verification_required
@csrf_protect
def answers(org_label, form_label, response_sid, question_label):
    ''' add notes to an answer
    much more limited than other (similar) routes
    no provision for viewing the answer on its own or for seeing all answers
    no provision for deleting answers
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
        flash('Form "%s" does not exist, sorry!' % form_label, 'warning')
        return redirect(url_for('organizations', org_label=org_label))
    form = forms[0]
        
    responses = Response.objects(call_sid=response_sid, form=form)
    if not responses:
        app.logger.error('%s tried to access a response that does not \
            exist' % session['email'])
        flash('Response "%s" does not exist, sorry!' % response_sid, 'warning')
        return redirect(url_for('responses', org_label=org_label
            , form_label=form_label))
    response = responses[0]

    questions = Question.objects(form=form, label=question_label)
    if not questions:
        app.logger.error('%s tried to access an question that does not \
            exist' % session['email'])
        flash('Question "%s" does not exist, sorry!' % question_label
            , 'warning')
        return redirect(url_for('responses', org_label=org_label
            , form_label=form_label, response_sid=response_sid))
    question = questions[0]
    
    answers = Answer.objects(response=response, question=question)
    if not answers:
        app.logger.error('%s tried to access an answer that does not \
            exist' % session['email'])
        flash('An answer to question "%s" does not exist for this response \
            , sorry!' % question_label, 'warning')
        return redirect(url_for('responses', org_label=org_label
            , form_label=form_label, response_sid=response_sid))
    answer = answers[0]

    if request.method == 'POST':
        form_type = request.form.get('form_type', '')
        if form_type == 'info':
            answer.notes = request.form.get('notes', '')
        else:
            # bad 'form_type'
            abort(404)
       
        try:
            answer.save()
            flash('Changes saved successfully.', 'success')
        except:
            answer.reload()
            app.logger.error('%s experienced an error saving info about the \
                answer to question "%s" for the response initiated at %s' \
                % (session['email'], question.name, response.initiation_time))
            flash('Error saving changes, sorry :/', 'error')
        
        return redirect(url_for('responses', org_label=org_label
            , form_label=form_label, response_sid=response_sid))
    
    if request.method == 'GET':
        if request.args.get('edit', '') == 'true':
            return render_template('answer_edit.html', answer=answer)

        else:
            flash('View the answer in the table below.', 'info')
            return redirect(url_for('responses', org_label=org_label
                , form_label=form_label, response_sid=response_sid))
