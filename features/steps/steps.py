from ivrhub import app
from lettuce import *

@step('I am not logged in')
def not_logged_in(step):
    world.app.get('logout', follow_redirects=True)


@step('I am logged in as an admin')
def logged_in_as_admin(step):
    world.app.post('/login', data=dict(
        email=app.config['INITIAL_USER']['email']
        , password=app.config['INITIAL_USER']['password']))

    
@step('I login with "(.*)" and "(.*)" appended to the default credentials')
def login_with_parameters_appended_to_default_credentials(step, a, b):
    response = world.app.post('/login'
        , data=dict(
            email=app.config['INITIAL_USER']['email'] + a
            , password=app.config['INITIAL_USER']['password'] + b
        ), follow_redirects=True)
    world.response_code = response.status_code
    world.response_data = response.data


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


@step('I go to the address "(.*)"')
def go_to_the_address(step, route):
    response= world.app.get(route, follow_redirects=True)
    world.response_code = response.status_code
    world.response_data = response.data


@step('I get the response code (\d+) and the page contains "(.*)"')
def get_a_response_code(step, expected_code, expected_data):
    expected_code = int(expected_code)
    expected_data = str(expected_data)
    assert world.response_code == expected_code, \
        "Got %s" % world.response_code
    assert expected_data in world.response_data
