# -*- coding: utf-8 -*-
from lettuce import step
from lettuce import world
from nose.tools import assert_equals, assert_is_not_none

@step(u'Given situation "([^"]*)"')
def given_situation_group1(step, situation):
    world.load_data(situation)
    world.login_admin()
@step(u'When I am on ([^"]*)')
def when_i_am_on_page(step, page):
    world.goto_page(page)
@step(u'And I click ([^"]*)')
def and_i_click_the_group1_button(step, group1):
    world.find_element(group1).click()
@step(u'And I select state ([^"]*)')
def and_i_select_state(step, state):
    world.browser.find_by_css("select[name='state']")[0].select(3)
    world.browser.is_text_present('line-through' , wait_time=2)
@step(u'Then I can move with link to ([^"]*) page')
def then_i_can_move_with_link_to_certain_page(step, name):
    link = world.get_page_url(name)
    assert world.browser.is_element_present_by_css('a[href="%s"]:not(.detail_url)' % link)
@step(u'Then ([^"]*) informs about ([^"]*)')
def then_link_informs_about_what(step, link, what):
    #XXX: Firefox does not support mouse_over. too bad
    from stables.models import Ticket
    TITLES = { 'cash': 'Cash', 'ticket': str(Ticket.objects.latest('id'))}
    world.browser.is_text_present(TITLES[what], wait_time=10)
    #el = world.find_element(link)
    #el.mouse_over()
    #tooltip = world.find_element(".tooltip")
    #assert_equals(tooltip.text, TITLES[what])
@step(u'And the rider has 1 unused ticket')
def and_the_user_has_1_unused_ticket(step):
    from stables.models import RiderInfo
    assert_equals(RiderInfo.objects.get(pk=1).unused_tickets.count(), 1)
@step(u'And the participation is paid with cash')
def and_the_participation_is_paid_with_cash(step):
    from stables.models import pay_participation
    from stables.models import Participation
    pay_participation(Participation.objects.latest('id'))
@step(u'And the rider has 1 used ticket')
def and_the_rider_has_1_used_ticket(step):
    from stables.models import Ticket
    assert_is_not_none(Ticket.objects.get(pk=1).transaction)
@step(u'And there is no pay buttons present')
def and_there_is_no_pay_buttons_present(step):
    assert not world.browser.is_element_present_by_css('.popover-content button')
