Feature: Proper response codes
    In order to try the testing setup
    As a beginner
    We'll see if routes return the correct response codes

    Scenario Outline: Response codes
        Given I have the route <route>
        When I go to the address
        Then I get the response code <code>

    Examples:
            | route  | code |
            | "/"    | 200  |
            | "nope" | 404  |
