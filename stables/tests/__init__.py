from datetime import datetime

def d(date):
    return datetime.strptime(date, '%Y-%m-%d')

def t(t):
    return datetime.strptime(t, '%H:%M').time()

def dt(dtime):
    return datetime.strptime(dtime, '%Y-%m-%d %H:%M')

