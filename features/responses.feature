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
            | "/"          | 200  | "a Flask skeleton" |
            | "about"      | 200  | "There are two roles" |
            | "help"       | 200  | "For more info on the project" |
            | "demo"       | 200  | "likely a youtube video" |
            | "register"   | 200  | "<legend>Register" |
            | "forgot/"    | 200  | "<legend>Forgotten Password" |
            | "nope"       | 404  | "" |
            | "login"      | 200  | "<legend>Login" |
            | "logout"     | 200  | "a Flask skeleton" |
            | "dashboard"  | 200  | "<legend>Login" |
            | "profile"    | 200  | "<legend>Login" |
            | "directory"  | 404  | "" |


    Scenario Outline: Response codes logged in as an admin
        Given I am logged in as an admin
        When I go to the address <route>
        Then I get the response code <code> and the page contains <data>

    Examples:
            | route        | code | data |
            | "/"          | 200  | "a Flask skeleton" |
            | "about"      | 200  | "There are two roles" |
            | "help"       | 200  | "For more info on the project" |
            | "demo"       | 200  | "likely a youtube video" |
            | "register"   | 200  | "Dashboard" |
            | "forgot/"    | 200  | "Dashboard" |
            | "nope"       | 404  | "" |
            | "login"      | 200  | "Dashboard" |
            | "logout"     | 200  | "a Flask skeleton" |
            | "dashboard"  | 200  | "Dashboard" |
            | "profile"    | 200  | "Editing" |
            | "directory"  | 200  | "Member Directory" |
