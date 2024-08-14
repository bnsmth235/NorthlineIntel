import locale

from django import template
from ..models import Check

register = template.Library()

@register.filter
def sum_values(queryset, attribute):
    return sum(getattr(obj, attribute) for obj in queryset)

@register.filter
def make_list(num):
    return [None] * num

@register.filter
def sub(a, b):
    return b - a

@register.filter(name='currency')
def currency(value):
    try:
        locale.setlocale(locale.LC_ALL,'en_US.UTF-8')
    except:
        locale.setlocale(locale.LC_ALL,'')
    loc = locale.localeconv()
    return locale.currency(value, loc['currency_symbol'], grouping=True)