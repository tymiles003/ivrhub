''' mongoengine models
'''
from mongoengine import *


class User(Document):
    ''' some are admins some are not
    '''
    admin_rights = BooleanField(required=True)
    api_id = StringField()
    api_key = StringField()
    email = EmailField(required=True, unique=True, max_length=254)
    email_confirmation_code = StringField(required=True)
    email_confirmed = BooleanField(required=True)
    forgot_password_code = StringField()
    last_login_time = DateTimeField(required=True)
    name = StringField()
    organizations = ListField(ReferenceField('Organization'))
    password_hash = StringField(required=True)
    registration_time = DateTimeField(required=True)
    verified = BooleanField(required=True)


class Organization(Document):
    ''' people join orgs
    '''
    description = StringField(default='')
    # url-safe version of the name
    label = StringField(unique=True, required=True)
    location = StringField(default='')
    name = StringField(unique=True, required=True)


class Form(Document):
    ''' the heart of the system
    '''
    # unique code for requesting this form via sms or a call
    calling_code = StringField()
    creation_time = DateTimeField()
    creator = ReferenceField(User)
    description = StringField(default = '')
    # url-safe version of the name
    label = StringField(unique_with='organization')
    language = StringField(default = '')
    name = StringField(unique_with='organization')
    organization = ReferenceField(Organization)
    # have to store questions here as well so we know the order
    questions = ListField(ReferenceField('Question'))


class Question(Document):
    ''' connected to forms
    '''
    audio_filename = StringField()
    audio_url = StringField()
    creation_time = DateTimeField()
    description = StringField()
    form = ReferenceField(Form)
    # url-safe version of the name
    label = StringField(unique_with='form')
    name = StringField(unique_with='form')
    # 'text_prompt', 'audio_file' or 'audio_url'
    prompt_type = StringField(default='text_prompt')
    # 'keypad' or 'voice' or 'no response'
    response_type = StringField(default='keypad')
    s3_key = StringField()
    s3_url = StringField()
    text_prompt = StringField()
    text_prompt_language = StringField(default='en')


class Response(Document):
    ''' individual response to a form
    '''
    call_sid = StringField()
    completion_time = DateTimeField()
    form = ReferenceField(Form)
    # whether this was a 'call' or 'ringback' or 'scheduled call'
    initiated_using = StringField()
    initiation_time = DateTimeField()
    # track the progress of the response
    last_question_asked = ReferenceField(Question)
    # any notes about the response as a whole
    notes = StringField()
    respondent_phone_number = StringField()


class Answer(Document):
    ''' connected to questions and responses
    '''
    audio_url = StringField()
    keypad_input = StringField()
    # any notes on this answer (like a transcription)
    notes = StringField()
    question = ReferenceField(Question)
    response = ReferenceField(Response)
