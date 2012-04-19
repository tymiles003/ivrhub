Feature: Registration mechanism catches common problems
    In order to test the registration mechanism
    As a beginner
    We'll see how the registration system responds to common issues

    Scenario: Registration fails when using an address that's already in the system 
        Given I am not logged in
        When I intend to register with the default values
        And I register with the saved data
        Then I get the response code 200 and the page contains "registered already"
    
    Scenario: Registration fails when using passwords that do not match
        Given I am not logged in
        When I intend to register with the default values
        And I intend to register with the "password" "goodday!"
        And I register with the saved data
        Then I get the response code 200 and the page contains "passwords did not match"
