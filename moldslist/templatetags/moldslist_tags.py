__author__ = 'torn'
from django import template
from django.core.urlresolvers import reverse
register = template.Library()


@register.simple_tag(takes_context=True)
def active(context, url_name):
    import re
    request = context['request']
    url = reverse(url_name)
    if url == request.path:
        return 'active'
    return ''


@register.filter
def format_date(date, time_format):
    date_repr =date.strftime(time_format)
    return date_repr

@register.filter
def format_delta(delta):
    days, remainder = divmod(delta.seconds, 3600*24)
    hours, remainder = divmod(remainder, 60*60)
    minutes, seconds = divmod(remainder, 60)
    if days > 0:
        day_str = '%i дней' % days
    else:
        day_str = ''

    if hours > 0:
        hour_str = ' %i часов' % hours
    else:
        hour_str = ''

    if minutes > 0:
        minute_str = ' %i минут' % minutes
    elif hour_str == '' and day_str == '':
        minute_str = '< 1 минуты'
    else:
        minute_str = ''
    return day_str + minute_str + hour_str



@register.filter
def add_attrs(field, css):
    attrs = {}
    definition = css.split(',')

    for d in definition:
        if ':' not in d:
            attrs['class'] = d
        else:
            t, v = d.split(':')
            attrs[t] = v

    return field.as_widget(attrs=attrs)