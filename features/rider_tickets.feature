Feature: Tickets shown in rider page
    Background: Given situation "rider with expired tickets"

    Scenario: Upkeeper goes to see user details
        When I am on the rider page
        Then rider unused valid tickets amount is shown
        And rider unused expired tickets amount is shown
