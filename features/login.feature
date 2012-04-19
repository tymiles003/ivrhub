Feature: Login mechanism accepts and rejects certain combinations
    In order to test the login mechanism
    As a beginner
    We'll see how the login system responds to certain inputs

    Scenario Outline: Login with certain credentials
        Given I am not logged in
        When I login with <a> and <b> appended to the default credentials
        Then I get the response code <code> and the page contains <data>

    Examples:
            | a      | b      | code | data |
            | ""     | ""     | 200  | "Dashboard"
            | "asdf" | ""     | 200  | "not a valid email address or password"
            | ""     | "asdf" | 200  | "not a valid email address or password"
            | "asdf" | "asdf" | 200  | "not a valid email address or password"
