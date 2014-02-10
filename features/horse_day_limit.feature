Feature: Horse day limit
    Background: Given situation "multiple events"

    Scenario: Horse limit is already topped
        Given Horse1 is attending on 3 events
        When I am on the dashboard
        Then Horse1 has a warning on it today
        And Horse1 has no warning on it tomorrow

    Scenario: Already topped horse limit is reduced
        Given Horse1 is attending on 3 events
        When I am on the dashboard
        And I change Horse1 to Horse2 in first participation
        Then Horse1 has no warning on it today
