# -*- coding: utf-8 -*-
from lettuce import step
from lettuce import world
from nose import tools

@step(u'rider unused ([^"]*) amount is shown')
def then_rider_unused_ticket_amount_is_shown(step, tickets):
    elem = world.find_element(tickets)
    tools.assert_in('2 pcs', elem.text)
