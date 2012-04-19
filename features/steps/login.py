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
