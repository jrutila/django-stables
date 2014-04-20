from datetime import datetime
import pytz
from django.conf import settings

def d(date):
    return datetime.strptime(date, '%Y-%m-%d')

def t(t):
    return datetime.strptime(t, '%H:%M').time()

def dt(dtime):
    return pytz.timezone(settings.TIME_ZONE).localize(datetime.strptime(dtime, '%Y-%m-%d %H:%M'))

