Feature: Registration mechanism catches common problems
    In order to test the registration mechanism
    As a beginner
    We'll see how the registration system responds to common actions

    
    Scenario: Registration fails when using passwords that do not match
        Given I am not logged in
        When I intend to register with the test account
        And I intend to register with the "password" "goodday!"
        And I register with the saved data
        Then I get the response code 200 and the page contains "passwords did not match"


    Scenario: Registration succeeds when email address is unique
        Given I am not logged in
        When I intend to register with the test account
        And I register with the saved data
        Then I get the response code 200 and the page contains "Thanks for signing up!"
    
    
    Scenario: Registration fails when using an address that's already in the system 
        Given I am not logged in
        When I intend to register with the test account
        And I register with the saved data
        Then I get the response code 200 and the page contains "registered already"
