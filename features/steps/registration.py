from hawthorne import app
from lettuce import *

@step('I intend to register with the test account')
def intend_to_register_with_test_account(step):
    # init the data container
    world.registration_data = dict()

    # save the defaults
    user = app.config['TEST_USER']
    world.registration_data['name'] = user['name']
    world.registration_data['email'] = user['email']
    world.registration_data['organization'] = user['organization']
    world.registration_data['password'] = user['password']
    world.registration_data['retype_password'] = user['password']


@step('I intend to register with the "(.*)" "(.*)"')
def intend_to_register_with_parameter(step, parameter, value):
    world.registration_data[parameter] = value


@step('I register with the saved data')
def register_with_saved_data(step):
    response = world.app.post('/register', data=world.registration_data
        , follow_redirects=True)
    world.response_code = response.status_code
    world.response_data = response.data
