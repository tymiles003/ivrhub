Feature: Proper response codes
    In order to try the testing setup
    As a beginner
    We'll see if routes return the correct response codes

    Scenario Outline: Response codes
        Given I have the route <route>
        When I go to the address
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
