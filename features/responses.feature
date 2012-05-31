Feature: Proper response codes when in various states of logged-in-edness
    In order to try the testing setup
    As a beginner
    We'll see if routes return the correct response codes

    Scenario Outline: Response codes when not logged in
        Given I am not logged in
        When I go to the address <route>
        Then I get the response code <code> and the page contains <data>

    Examples:
            | route        | code | data |
            | "/"          | 200  | "mobile data collection" |
            | "about"      | 200  | "conduct surveys" |
            | "help"       | 200  | "For more info" |
            | "demo"       | 200  | "Check back soon" |
            | "register"   | 200  | "<legend>Register" |
            | "forgot/"    | 200  | "<legend>Forgotten Password" |
            | "nope"       | 404  | "" |
            | "login"      | 200  | "<legend>Login" |
            | "logout"     | 200  | "mobile data collection" |
            | "dashboard"  | 200  | "<legend>Login" |
            | "profile"    | 200  | "<legend>Login" |
            | "members"  | 404  | "" |


    Scenario Outline: Response codes logged in as an admin
        Given I am logged in as an admin
        When I go to the address <route>
        Then I get the response code <code> and the page contains <data>

    Examples:
            | route        | code | data |
            | "/"          | 200  | "mobile data collection" |
            | "about"      | 200  | "conduct surveys" |
            | "help"       | 200  | "For more info" |
            | "demo"       | 200  | "Check back soon" |
            | "register"   | 200  | "Dashboard" |
            | "forgot/"    | 200  | "Dashboard" |
            | "nope"       | 404  | "" |
            | "login"      | 200  | "Dashboard" |
            | "logout"     | 200  | "mobile data collection" |
            | "dashboard"  | 200  | "Dashboard" |
            | "profile"    | 200  | "edit" |
            | "profile?edit=true"    | 200  | "Modify" |
            | "members"  | 200  | "Members" |
