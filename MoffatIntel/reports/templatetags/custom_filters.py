from django import template
from ..models import Invoice, Check

register = template.Library()

@register.filter
def sum_values(queryset, attribute):
    return sum(getattr(obj, attribute) for obj in queryset)

@register.simple_tag
def calculate_invoice_total(group, subgroup, draw):
    filtered_invoices = Invoice.objects.filter(group_id=group, subgroup_id=subgroup, draw_id=draw)
    total = sum(filtered_invoices.values_list('invoice_total', flat=True))
    return total

@register.filter
def make_list(num):
    return [None] * num

@register.filter
def sub(a, b):
    return b - a

@register.simple_tag
def calculate_percentage(group, subgroup, draw):
    dividend = calculate_checks_total(group, subgroup, draw)
    divisor = calculate_invoice_total(group, subgroup, draw)
    try:
        percent = (dividend / divisor) * 100
    except:
        return 0
    return percent

@register.simple_tag
def calculate_checks_total(group, subgroup, draw):
    subgroup_invoices = Invoice.objects.filter(group_id=group, subgroup_id=subgroup, draw_id=draw)
    related_checks = Check.objects.filter(invoice_id__in=subgroup_invoices)
    total = sum(related_checks.values_list('check_total', flat=True))
    return total