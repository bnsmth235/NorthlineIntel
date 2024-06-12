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