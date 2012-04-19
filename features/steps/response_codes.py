from serve.hawthorne_server import app
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


@step('I register with the email address "(.*)"')
def register_with_email_address(step, address):
    if address == 'default':
        email = app.config['INITIAL_USER']['email']

    response = world.app.post('/register'
        , data=dict(
            email=email
            , password=app.config['INITIAL_USER']['password']
            , retype_password=app.config['INITIAL_USER']['password']
        ), follow_redirects=True)
    world.response_code = response.status_code
    world.response_data = response.data


@step('I register with passwords that do not match')
def register_with_passwords_that_do_not_match(step):
    response = world.app.post('/register'
        , data=dict(
            email=app.config['INITIAL_USER']['password']
            , password='s3cr3t'
            , retype_password='h1dd3n'
        ), follow_redirects=True)
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
