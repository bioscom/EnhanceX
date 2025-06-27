import re 

from django import template
register = template.Library()

@register.filter
def currency(value):
    try:
        return "{:,.2f}".format(value)
    except (ValueError, TypeError):
        return value
    

@register.filter
def dollar_currency(value):
    try:
        return "${:,.2f}".format(value)
    except (ValueError, TypeError):
        return value
    

@register.filter
def replace ( string, args ): 
    search  = args.split(args[0])[1]
    replace = args.split(args[0])[2]

    return re.sub( search, replace, string )   

#^[a-zA-Z]+[a-zA-Z0-9_-]*(?:,[a-zA-Z]+[a-zA-Z0-9_-]*)*$