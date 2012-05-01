from lettuce import *

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
