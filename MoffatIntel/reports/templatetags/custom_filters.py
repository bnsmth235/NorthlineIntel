from django import template

register = template.Library()

@register.filter
def sum_values(queryset, attribute):
    return sum(getattr(obj, attribute) for obj in queryset)
