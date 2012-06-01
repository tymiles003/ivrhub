''' response_views
viewing responses to forms
'''
from flask import (render_template, request, flash, redirect, url_for, session
    , abort)

from decorators import *
from models import *
import utilities
from ivrhub import app


response_route = '/organizations/<org_label>/forms/<form_label>/responses'
@app.route(response_route, defaults={'response_sid': None})
@app.route(response_route + '/<response_sid>', methods=['GET', 'POST'])
@verification_required
@csrf_protect
def responses(org_label, form_label, response_sid):
    ''' show the responses
    if there's a call SID included in the route, render that response alone
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

    if request.method == 'POST':
        if not response_sid:
            abort(404)

        responses = Response.objects(call_sid=response_sid, form=form)
        if not responses:
            abort(404)
        response = responses[0]

        form_type = request.form.get('form_type', '')
        if form_type == 'info':
            response.notes = request.form.get('notes', '')

        elif form_type == 'admin':
            initiation_time = response.initiation_time.strftime(
                '%m/%d/%y %H:%M:%S')
            utilities.delete_response(response)

            app.logger.info('%s deleted response initiated at %s' \
                % (session['email'], initiation_time))
            flash('The response initiated at %s was deleted' \
                % initiation_time, 'success')
            return redirect(url_for('responses', org_label=org.label
                , form_label=form.label))
        
        else:
            # bad 'form_type'
            abort(404)
       
        try:
            response.save()
            flash('Changes saved successfully.', 'success')
        except:
            response.reload()
            app.logger.error('%s experienced an error saving info about the \
                response initiated at %s' % (session['email']
                , response.initiation_time))
            flash('Error saving changes, sorry :/', 'error')
        
        return redirect(url_for('responses', org_label=org.label
            , form_label=form.label, response_sid=response.call_sid
            , edit='true'))

    
    if request.method == 'GET':
        if response_sid:
            responses = Response.objects(call_sid=response_sid, form=form)
            if not responses:
                flash('Response "%s" not found, sorry!' % response_sid
                    , 'warning')
                return redirect(url_for('responses', org_label=org.label
                    , form_label=form.label))
            response = responses[0]

            if request.args.get('edit', '') == 'true':
                return render_template('response_edit.html', response=response)

            else:
                # get all relevant answers
                # make sure they're ordered correctly
                ordered_answers = []
                answers = Answer.objects(response=response)
                for question in form.questions:
                    for answer in answers:
                        if answer.question == question:
                            ordered_answers.append(answer)
                            continue

                # calculate the duration of the response
                if response.completion_time:
                    delta = response.completion_time - response.initiation_time
                    # format the difference like "03:45"
                    call_minutes = delta.seconds/60
                    call_seconds = delta.seconds%60
                    # see if we need to prepend any zeros
                    if call_minutes < 10:
                        call_minutes = '0%s' % call_minutes
                    
                    if call_seconds < 10:
                        call_seconds = '0%s' % call_seconds

                    call_duration = '%s:%s' % (call_minutes, call_seconds)

                else:
                    call_duration = None

                return render_template('response.html', response=response
                    , answers=ordered_answers, call_duration=call_duration)
        
        else:
            # no response in particular was specified; show em all
            responses = Response.objects(form=form).order_by(
                '-initiation_time')
            return render_template('form_responses.html', responses=responses
                , form=form)
