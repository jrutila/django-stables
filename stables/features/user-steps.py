# -*- coding: utf-8 -*-
from lettuce import step
from django.contrib.auth.models import User
from lettuce import world
from lettuce.django import django_url

@step(u'a user exists with username \'([^\']*)\' and password \'([^\']*)\'')
def a_user_exists_with_username_and_password(step, username, password):
    User.objects.create_user(username, '', password)

@step(u'I got to the \'([^\']*)\' page')
def i_got_to_the_page(step, url):
    world.browser.visit(django_url(url))

@step(u'I fill in \'([^\']*)\' with \'([^\']*)\'')
def i_fill_in_group1_with_group2(step, field, value):
    world.browser.fill(field, value)

@step(u'I click button \'([^\']*)\'')
def i_click_button_text(step, text):
    world.browser.find_by_xpath("//*[contains(text(), '%s')]" % text)[1].click()
    
@step(u'Then I should see "([^"]*)"')
def then_i_should_see_text(step, text):
    world.browser.is_text_present(text, wait_time=10)

