from lettuce import before, after, world
from splinter.browser import Browser
from django.test.utils import setup_test_environment, teardown_test_environment
from django.core.management import call_command
from django.db import connection
from django.conf import settings
from lettuce.django import django_url
from django.core.urlresolvers import reverse
import re

DATA = {
        'ticketpaid participation': 'fixtures/harvest.json',
        }

PAGES = {
        'the participation ([^"]*) details': 'view_participation',
        'the dashboard': 'newboard',
        }

LINKS = {
        'the participation link': '.detail_url',
        'the cash button': 'button[value="0"]',
        'the ticket button': 'button[value="1"]',
        }

@before.harvest
def initial_setup(server):
    call_command('syncdb', interactive=False, verbosity=0)
    call_command('flush', interactive=False, verbosity=0)
    call_command('loaddata', 'all', verbosity=0)
    setup_test_environment()
    world.browser = Browser('firefox')

@after.harvest
def cleanup(server):
    connection.creation.destroy_test_db(settings.DATABASES['default']['NAME'])
    #teardown_test_environment()

@before.each_scenario
def reset_data(scenario):
    # Clean up django.
    call_command('flush', interactive=False, verbosity=0)

@after.all
def teardown_browser(total):
    world.browser.quit()

@world.absorb
def load_data(name):
    call_command('loaddata', DATA[name], verbosity=0)

@world.absorb
def login_admin(name='admin'):
    pass

@world.absorb
def find_element(name):
    assert name in LINKS
    return world.browser.find_by_css(LINKS[name])[0]

@world.absorb
def get_page_url(name):
    for p,view in PAGES.items():
        gr = re.match(p, name)
        if gr:
            return reverse(view, args=gr.groups())

@world.absorb
def goto_page(name, *args):
    assert name in PAGES
    if name == 'the dashboard':
        world.browser.visit(django_url(reverse(PAGES[name], *args)+"#2014-01-09"))
    else:
        world.browser.visit(django_url(reverse(PAGES[name], *args)))
    world.browser.reload()
