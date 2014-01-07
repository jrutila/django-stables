Feature: User account features
    Scenario: User enters wrong password
        Given a user exists with username 'joeb' and password 'beoj'
        When I got to the '/accounts/login' page
        And I fill in 'username' with 'joeb'
        And I fill in 'password' with 'invalid'
        And I click button 'Log in'
        Then I should see "Your username and password didn't match."
