from django import template
from django.conf import settings
from decimal import Decimal

register = template.Library()

def reference_check_number(ref):
    multipliers = (7, 3, 1)
    ref = ref.replace(' ', '')
    inverse = map(int, ref[::-1])
    summ = sum(multipliers[i % 3] * x for i, x in enumerate(inverse))
    return (10 - (summ % 10)) % 10

def split_human_readale(s, n):
    inverse = s[::-1]
    parts = [(' ' if i and i % n == 0 else '') + c for i, c in enumerate(inverse)]
    return ''.join(parts)[::-1]

@register.filter
def bank_reference(trid):
    check = reference_check_number(trid)
    ref = trid + str(check)
    return split_human_readale(ref, 5)

@register.filter
def add_vat(value):
    TWO = Decimal(10) ** -2
    final = value*(1+settings.SHOP_VAT)
    return final.quantize(TWO)

@register.filter
def orderproducts(products):
    return sorted(products, key=lambda p: p.name.lower())
