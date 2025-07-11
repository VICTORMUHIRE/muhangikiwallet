from django import template

register = template.Library()

@register.filter
def sub(value, arg):
    try:
        return value - arg
    except (TypeError, ValueError):
        return ''
    
@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (TypeError, ValueError):
        return ''
    
@register.filter
def div(value, arg):
    try:
        return float(value) / float(arg)
    except (TypeError, ValueError):
        return ''