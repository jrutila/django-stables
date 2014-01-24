Feature: Payment dialog feature
    Scenario: Upkeeper goes to see participation details
        Given situation "ticketpaid participation"
        When I am on the dashboard
        And I click the participation link
        Then I can move with link to the participation 1 details page

    Scenario: Upkeeper changes to cash payment
        Given situation "ticketpaid participation"
        When I am on the dashboard
        And I click the participation link
        And I click the cash button
        Then the participation link informs about cash
        And the rider has 1 unused ticket

    Scenario: Upkeeper changes to ticket payment
        Given situation "ticketpaid participation"
        And the participation is paid with cash
        When I am on the dashboard
        And I click the participation link
        And I click the ticket button
        Then the participation link informs about ticket
        And the rider has 1 used ticket

    Scenario: Upkeeper canceles participation
        Given situation "ticketpaid participation"
        When I am on the dashboard
        And I select state "Canceled"
        And I click the participation link
        Then I can move with link to the participation 1 details page
        And there is no pay buttons present
        And the rider has 1 unused ticket
