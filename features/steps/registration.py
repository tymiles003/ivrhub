from serve.hawthorne_server import app
from lettuce import *

@step('I intend to register with the default values')
def intend_to_register_with_defaults(step):
    # init the data container
    world.registration_data = dict()

    # save the defaults
    default = app.config['INITIAL_USER']
    world.registration_data['name'] = default['name']
    world.registration_data['email'] = default['email']
    world.registration_data['organization'] = default['organization']
    world.registration_data['password'] = default['password']
    world.registration_data['retype_password'] = default['password']


@step('I intend to register with the "(.*)" "(.*)"')
def intend_to_register_with_parameter(step, parameter, value):
    world.registration_data[parameter] = value


@step('I register with the saved data')
def register_with_saved_data(step):
    response = world.app.post('/register', data=world.registration_data
        , follow_redirects=True)
    world.response_code = response.status_code
    world.response_data = response.data
