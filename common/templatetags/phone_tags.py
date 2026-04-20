from django import template

from common.phone import format_phone as _format_phone

register = template.Library()


@register.filter(name='format_phone')
def format_phone_filter(value):
    return _format_phone(value)
