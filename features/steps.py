# -*- coding: utf-8 -*-
from lettuce import step
from lettuce import world
from stables.models import Horse
from stables.models import Participation

@step(u'Given ([^"]*) is attending on 3 events')
def given_horse_is_attending_on_3_events(step, horsename):
    Participation.objects.update(horse=Horse.objects.get(name=horsename))
@step(u'([^"]*) has ([^"]*) warning on it ([^"]*)')
def then_horse_has_a_warning_on_it(step, horsename, isit, when):
    if when == 'today': nth = 0
    else: nth = 3
    ch = world.find_element('horse chooser', nth)
    assert ch.has_class('warning') == (isit == 'a')
@step(u'And I change Horse1 to Horse2 in first participation')
def and_i_change_horse1_to_horse2_in_first_participation(step):
    ch = world.find_element('horse chooser')
    ch.select(2)
