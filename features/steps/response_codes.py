from lettuce import *

@step('I have the route "(.*)"')
def have_the_route(step, route):
    route = str(route)
    world.route = route

@step('I go to the address')
def go_to_the_address(step):
    world.response_code = world.app.get(world.route).status_code

@step('I get the response code (\d+)')
def get_a_response_code(step, expected):
    expected = int(expected)
    assert world.response_code == expected, \
        "Got %s" % world.response_code

