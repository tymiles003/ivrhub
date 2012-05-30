''' incoming_views
handling interaction with voice and sms provider
'''

from flask import (render_template, request, flash, redirect, url_for, session
    , abort, escape)

from decorators import *
from models import *
import utilities
from ivrhub import app

@app.route('/incoming/<interaction_type>', methods=['GET', 'POST'])
def incoming(interaction_type):
    ''' handles twilio interaction
    '''
    if interaction_type == 'sms':
        # find the requested form
        forms = Form.objects(calling_code=request.form.get('Body'))
        twiml_response = twiml.Response()
        if not forms:
            # reply 'not found'
            twiml_response.sms('requested form not found, sorry'
                , to = request.form.get('From')
                , sender = app.config['TWILIO']['verified_number'])
        else:
            # check form status
            form = forms[0]
            if not form.accepting_submissions:
                twiml_response.sms('this form is not currently accepting \
                    responses', to = request.form.get('From')
                    , sender = app.config['TWILIO']['verified_number'])
        else:
            # ringback: make the call - can't use twiml to initiate
            call = twilio_client.calls.create(
            to = request.form.get('From')
                , from_ = app.config['TWILIO']['verified_number']
                , url = urlparse.urljoin(app.config['APP_ROOT']
                , url_for('incoming', interaction_type='voice')))
    
            # make a new response, saving the SID
            try:
                new_response = Response(
                    call_sid = call.sid
                    , initiated_using = 'ringback'
                    , initiated_at = datetime.datetime.utcnow()
                    , respondent_phone_number = request.form.get('From')
                    , form = form
                )
                new_response.save()
                form.update(push__responses=new_response)
            except:
                abort(404)

            return str(twiml_response)

    elif interaction_type == 'voice':
        # reply to ringbacks or fresh calls
        twiml_response = twiml.Response()
        responses = Response.objects(call_sid = request.form.get('CallSid'))

        if not responses:
            if not request.form.get('Digits'):
                # this is a fresh call
                with twiml_response.gather() as g:
                    g.say('hello, please enter your form calling code and \
                        then press pound')
                    return str(twiml_response)
                else:
                    # someone called in and has entered their form's calling code
                    forms = Form.objects(calling_code=request.form.get('Digits'))
                    if not forms:
                        twiml_response.say('sorry, we cannot find an available \
                            form with the calling code %s' %
                            request.form.get('Digits'))
                        return str(twiml_response)
                            
                    form = forms[0]
                    if not form.accepting_submissions:
                        twiml_response.say('this form is not currently \
                            accepting responses')
                        return str(twiml_response)
                                    
                # make a new response, saving the SID
                try:
                    new_response = Response(
                        call_sid = request.form.get('CallSid')
                        , initiated_using = 'call'
                        , initiated_at = datetime.datetime.utcnow()
                        , respondent_phone_number = request.form.get('From')
                        , form = form
                    )
                    new_response.save()
                    form.update(push__responses=new_response)
                except:
                    twiml_response.say('there has been an error, sorry')
                    return str(twiml_response)

# ask the first question
                    if not new_response.form.questions:
                                            twiml_response.say('there are no questions for the form \
                                                                            called %s, sorry' % new_response.form.name)
                                                            else:
                                                                                    twiml_response.say('Hello.  This form is called %s. \
                                                                                                                    First question.' % new_response.form.name)
                                                                                                        # build up the twiml with the first question
                                                                                                                            twiml_response = _build_question_twiml(
                                                                                                                                                            new_response.form.questions[0], twiml_response)
                                                                                                                                                # bump the last question
                                                                                                                                                                    new_response.update(set__last_question_asked = \
                                                                                                                                                                                                    new_response.form.questions[0])

                                                                                                                                                                                    return str(twiml_response)

                                                                                                                                                                                        else:
                                                                                                                                                                                                        # this is the start of ringback or a continuing response
                                                                                                                                                                                                                    response = responses[0]
                                                                                                                                                                                                                                if not response.last_question_asked:
                                                                                                                                                                                                                                                    # no questions have been asked, must be the start of ringback
                                                                                                                                                                                                                                                                    if not response.form.questions:
                                                                                                                                                                                                                                                                                            twiml_response.say('there are no questions for the form \
                                                                                                                                                                                                                                                                                                                            called %s, sorry' % response.form.name)
                                                                                                                                                                                                                                                                                                            else:
                                                                                                                                                                                                                                                                                                                                    twiml_response.say('Hello.  This form is called %s. \
                                                                                                                                                                                                                                                                                                                                                                    First question.' % response.form.name)
                                                                                                                                                                                                                                                                                                                                                        # build up the twiml with the first question
                                                                                                                                                                                                                                                                                                                                                                            twiml_response = _build_question_twiml(
                                                                                                                                                                                                                                                                                                                                                                                                            response.form.questions[0], twiml_response)
                                                                                                                                                                                                                                                                                                                                                                                                # bump the last question
                                                                                                                                                                                                                                                                                                                                                                                                                    response.update(
                                                                                                                                                                                                                                                                                                                                                                                                                                                    set__last_question_asked = response.form.questions[0])
                                                                                                                                                                                                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                                                                                                                                                                                    # a question has been asked and answered
                                                                                                                                                                                                                                                                                                                                                                                                                                                                    # parse the answer first
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    last_question = response.last_question_asked
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    new_answer = Answer(
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                question = last_question
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    , response_type = last_question.response_type)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    if last_question.response_type == 'keypad':
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            new_answer.raw_keypad_input = request.form.get('Digits')
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            elif last_question.response_type == 'voice':
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    new_answer.audio_url = request.form.get('RecordingUrl')
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    new_answer.save()
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    # push the new answer 
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    response.update(push__answers=new_answer)

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    index = response.form.questions.index(last_question)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    if (index + 1) == len(response.form.questions):
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            # if that was the last question, hangup
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                response.update(
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                set__completed_at = datetime.datetime.utcnow())
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    twiml_response.say('This form is complete.  Goodbye.')
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        twiml_response.hangup()
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        else:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                # ask the next question
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    # build up the twiml with the next question
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        next_question = response.form.questions[index+1]
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            twiml_response = _build_question_twiml(next_question
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            , twiml_response)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                # bump the last question asked
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    response.update(
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    set__last_question_asked = next_question)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                return str(twiml_response)

                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                else:
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            abort(404)


@app.route('/organizations/', defaults={'org_label': None})
@app.route('/organizations/<org_label>', methods=['GET', 'POST'])
@verification_required
def organizations(org_label):
    ''' show the organizations
    if there's a label included in the route, render that organization alone
    '''
    user = User.objects(email=session['email'])[0]

    if request.method == 'POST':
        orgs = Organization.objects(label=org_label)
        if not orgs:
            abort(404)
        org = orgs[0]
        
        # permission-check
        if org not in user.organizations and not user.admin_rights:
            app.logger.error('%s tried to edit an organization but was \
                denied for want of admin rights' % session['email'])
            abort(404)

        form_type = request.form.get('form_type', '')
        if form_type == 'info':
            if org.name != request.form.get('name', ''):
                app.logger.info('%s edited the name of %s to %s' % (
                    session['email'], org.name, request.form.get('name', '')))
                name = request.form.get('name', '')
                org.name = name
                org.label = str(escape(name).replace(' ', '-')).lower()
           
            if org.description != request.form.get('description', ''):
                app.logger.info('%s edited the description of %s to %s' % (
                    session['email'], org.name
                    , request.form.get('description', '')))
                org.description = request.form.get('description', '')
            
            if org.location != request.form.get('location', ''):
                app.logger.info('%s edited the location of %s to %s' % (
                    session['email'], org.name
                    , request.form.get('location', '')))
                org.location = request.form.get('location', '')

        elif form_type == 'add_members':
            # push membership
            target = request.form.get('add_member_email', '')
            new_members = User.objects(email=target)
            if not new_members:
                flash('we cannot find "%s", has it been registered?' % \
                    target, 'error')
                return redirect(url_for('organizations', org_label=org.label))

            new_member = new_members[0]
            # already a member?
            if org in new_member.organizations:
                flash('"%s" is already a member of "%s"' % (target, org.name)
                    , 'warning')
                return redirect(url_for('organizations', org_label=org.label))
            
            else:
                # add them
                new_member.update(push__organizations=org)
                flash('successfully added "%s" to "%s"' % (target, org.name)
                    , 'success')
                return redirect(url_for('organizations', org_label=org.label))
        
        elif form_type == 'remove_members':
            # push/pull membership
            target = request.form.get('remove_member_email', '')
            old_members = User.objects(email=target)
            if not old_members:
                flash('we cannot find "%s", has it been registered?' % \
                    target, 'error')
                return redirect(url_for('organizations', org_label=org.label))
            
            old_member = old_members[0]
            # not yet a member?
            if org not in old_member.organizations:
                flash('"%s" is not yet a member of "%s"' % (target, org.name)
                    , 'warning')
                return redirect(url_for('organizations', org_label=org.label))
            else:
                # drop 'em
                old_member.update(pull__organizations=org)
                flash('successfully removed "%s" from %s' % (target, org.name)
                    , 'info')
                return redirect(url_for('organizations', org_label=org.label))

        elif form_type == 'admin':
            # delete the organization; permission-check first
            if not user.admin_rights:
                app.logger.error('%s tried to delete %s but was denied for \
                    want of admin rights' % (session['email'], org.name))
                abort(404)

            # revoke membership first
            members = User.objects(organizations=org)
            for member in members:
                member.update(pull__organizations=org)

            # delete all associated forms
            forms = Form.objects(organization=org)
            for form in forms:
                utilities.delete_form(form)
            
            # blow away the org itself
            name = org.name
            org.delete()
            app.logger.info('%s deleted %s' % (session['email'], name))
            flash('organization "%s" was deleted' % name, 'success')
            return redirect(url_for('organizations'))
        
        else:
            # bad 'form_type'
            abort(404)
       
        try:
            org.save()
            flash('changes saved successfully', 'success')
        except:
            org.reload()
            app.logger.error('%s experienced an error saving info about %s' % (
                session['email'], request.form['name']))
            flash('Error saving changes, is the name unique?', 'error')
        
        return redirect(url_for('organizations', org_label=org.label
            , edit='true'))

    
    if request.method == 'GET':
        if org_label:
            orgs = Organization.objects(label=org_label)
            if not orgs:
                app.logger.error('%s tried to access an organization that \
                    does not exist' % session['email'])
                flash('Organization "%s" not found, sorry!' % org_label
                    , 'warning')
                return redirect(url_for('organizations'))
            org = orgs[0]

            # permission-check
            if org not in user.organizations and not user.admin_rights:
                app.logger.error('%s tried to access an organization but was \
                    denied for want of admin rights' % session['email'])
                abort(404)

            if request.args.get('edit', '') == 'true':
                users = User.objects(organizations=org)
                return render_template('organization_edit.html'
                    , organization=org, users=users)
            else:
                # get all the members
                users = User.objects(organizations=org)
                # get all relevant forms
                forms = Form.objects(organization=org)
                return render_template('organization.html', organization=org
                    , users=users, forms=forms)

        if request.args.get('create', '') == 'true':
            # create a new form
            # permissions-check 
            if not user.admin_rights:
                app.logger.error('%s tried to create an organization but was \
                    denied for want of admin rights' % session['email'])
                abort(404)

            try:
                org_name = 'org-%s' % utilities.generate_random_string(6)
                new_org = Organization(
                    label = org_name.lower()
                    , name = org_name
                )
                new_org.save() 
                app.logger.info('organization created by %s' % \
                    session['email'])
                flash('organization created; please change the defaults', 
                    'success')
            except:
                app.logger.error('organization creation failed for %s' % \
                    session['email'])
                flash('There was an error in the form, sorry :/', 'error')
                return redirect(url_for('organizations'))
            
            # redirect to the editing screen
            return redirect(url_for('organizations', org_label=new_org.label
                , edit='true'))
        
        # nobody in particular was specified; show em all
        if user.admin_rights:
            orgs = Organization.objects()
        else:
            orgs = user.organizations

        # find the users for each org
        users = {}
        for org in orgs:
            users[org.name] = User.objects(organizations=org)

        return render_template('organizations.html', organizations=orgs
            , users=users)
