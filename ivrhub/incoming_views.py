''' incoming_views
handling interaction with voice and sms provider (twilio, at the moment)
'''
import datetime
import urlparse

from flask import (request, url_for, abort)
from twilio.rest import TwilioRestClient
from twilio import twiml

from decorators import *
from models import *
from ivrhub import app

# create twilio rest client
twilio_client = TwilioRestClient(app.config['TWILIO']['account_sid']
    , app.config['TWILIO']['auth_token'])

def _build_question_twiml(question, twiml_response):
    ''' invokes twiml api as appropriate based on question type
    uses 'with' statement to allow interrupts for gather()
    interrupts not available for twilio's 'say'
    '''
    if question.response_type == 'keypad':
        with twiml_response.gather() as g:
            if question.prompt_type == 'text_prompt':
                g.say(question.text_prompt
                    , language=question.text_prompt_language)
            elif question.prompt_type == 'audio_url':
                g.play(question.audio_url)
            elif question.prompt_type == 'audio_file':
                g.play(question.s3_url)
            else:
                g.say('error, there is no prompt')

    elif question.response_type == 'voice':
        if question.prompt_type == 'text_prompt':
            twiml_response.say(question.text_prompt
                , language=question.text_prompt_language)
        elif question.prompt_type == 'audio_url':
            twiml_response.play(question.audio_url)
        elif question.prompt_type == 'audio_file':
            twiml_response.play(question.s3_url)
        else:
            twiml_response.say('error, there is no prompt')
        
        twiml_response.record()

    return twiml_response
                

def _ask_first_question(response, twiml_response):
    ''' ask the first question of a form
    '''
    if not response.form.questions:
        twiml_response.say('There are no questions for the form called %s, \
            sorry.' % response.form.name)
        twiml_response.hangup()
        return str(twiml_response)

    twiml_response.say('Hello.  This form is called %s. First question.' % 
        response.form.name)
    
    # build up the twiml with the first question
    twiml_response = _build_question_twiml(response.form.questions[0]
        , twiml_response)
    
    # bump the state of this response
    response.update(set__last_question_asked = response.form.questions[0])

    return twiml_response


@app.route('/incoming/<interaction_type>', methods=['GET', 'POST'])
def incoming(interaction_type):
    ''' handles twilio interaction
    '''
    if interaction_type == 'sms':
        # find the requested form
        forms = Form.objects(calling_code=request.form.get('Body', ''))
        twiml_response = twiml.Response()
        if not forms:
            # try to reply that the form was not found
            twiml_response.sms('requested form not found, sorry'
                , to = request.form.get('From', '')
                , sender = app.config['TWILIO']['verified_number'])
            return str(twiml_response)
        
        form = forms[0]
        # ringback -- call the person who texted in
        # create the call with twilio's rest client - can't use twiml
        endpoint = urlparse.urljoin(app.config['APP_ROOT']
            , url_for('incoming', interaction_type='voice'))
        call = twilio_client.calls.create(to = request.form.get('From')
            , from_ = app.config['TWILIO']['verified_number']
            , url = endpoint)

        # make a new response, saving the SID of the new call
        new_response = Response(
            call_sid = call.sid
            , initiated_using = 'ringback'
            , initiation_time = datetime.datetime.utcnow()
            , respondent_phone_number = request.form.get('From', '')
            , form = form)
        new_response.save()
        
        # return blank twiml response as reply to original SMS
        return str(twiml_response)

    elif interaction_type == 'voice':
        # reply to ringbacks or fresh calls
        twiml_response = twiml.Response()
        responses = Response.objects(call_sid = request.form.get('CallSid'))

        if not responses:
            if not request.form.get('Digits'):
                # this is a brand new call, find out what form they want
                with twiml_response.gather() as g:
                    g.say('Hello, please enter your form calling code and \
                        then press pound')
                    return str(twiml_response)
            
            else:
                # someone has entered their form's calling code
                # but has not yet started answering questions
                digits = request.form.get('Digits', '')
                forms = Form.objects(calling_code=digits)
                if not forms:
                    twiml_response.say('Sorry, we cannot find an available \
                        form with the calling code %s' % digits)
                    return str(twiml_response)
                        
                form = forms[0]
                # make a new response, saving the SID
                new_response = Response(
                    call_sid = request.form.get('CallSid', '')
                    , initiated_using = 'call'
                    , initiation_time = datetime.datetime.utcnow()
                    , respondent_phone_number = request.form.get('From', '')
                    , form = form
                )
                new_response.save()

                # ask the first question
                twiml_response = _ask_first_question(new_response
                    , twiml_response)

                return str(twiml_response)

        else:
            # responses were found so this is the start of ringback 
            # or a continuing response from a call-in
            response = responses[0]
            if not response.last_question_asked:
                # no questions have been asked 
                # must be the start of ringback, ask the first question
                twiml_response = _ask_first_question(response
                    , twiml_response)
                return str(twiml_response)

            
            # a question has been asked and answered
            last_question = response.last_question_asked
            # parse the answer to the previously-asked question
            new_answer = Answer(
                question = last_question
                , response = response
                , response_type = last_question.response_type)

            if last_question.response_type == 'keypad':
                new_answer.keypad_input = request.form.get('Digits')

            elif last_question.response_type == 'voice':
                new_answer.audio_url = request.form.get('RecordingUrl')

            new_answer.save()
            
            # see where we are in the question progression
            index = response.form.questions.index(last_question)
            if (index + 1) == len(response.form.questions):
                # that was the last question, hangup
                response.update(
                    set__completion_time = datetime.datetime.utcnow())
                twiml_response.say('This form is complete.  Goodbye.')
                twiml_response.hangup()
                return str(twiml_response)
            
            # ask the next question
            # build up the twiml with the next question
            next_question = response.form.questions[index+1]
            twiml_response = _build_question_twiml(next_question
                , twiml_response)
            # bump the last question asked
            response.update(set__last_question_asked = next_question)

            return str(twiml_response)

    else:
        # unknown 'interaction_type'
        abort(404)
