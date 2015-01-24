# encoding: utf-8

from xml.dom import minidom
import json_ as json


SECOND = 1
MINUTE = 60
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY
YEAR = 365 * DAY


def format_duration(s, verbose=False):
    s = int(s)
    days = int(s / DAY)
    s -= days * DAY
    hours = int(s / 3600)
    s -= hours * HOUR
    minutes = int(s / 60)
    s -= minutes * MINUTE
    seconds = s

    tokens = []
    if days > 0:
        tokens.append('{0}d'.format(days))
    if hours > 0:
        tokens.append('{0}h'.format(hours))
    if minutes > 0:
        tokens.append('{0}m'.format(minutes))
    if seconds > 0 or s == 0:
        tokens.append('{0}s'.format(seconds))

    if not verbose:
        tokens = tokens[:1]

    return ' '.join(tokens)


def format_number(number):
    try:
        float(number)
    except TypeError:
        return ''

    minus = float(number) < 0
    block_size = 3

    tokens = str(abs(number)).split('.')
    suffix = '.%s' % tokens[1] if len(tokens) > 1 else ''
    old_str = tokens[0]
    new_str = ''
    length = len(old_str)

    for i in range(length):
        index = length - 1 - i
        if i / block_size > 0 and i % 3 == 0:
            new_str += ','
        new_str += old_str[index]

    formatted = new_str[::-1] + suffix
    if minus:
        formatted = '-' + formatted
    return formatted


def format_percent(ratio):
    return '{0}%'.format(int(float(ratio) * 100))


def format_price(price, currency=u'₩'):
    return u'{currency} {price}'.format(
        currency=currency, price=format_number(price))


def format_phone(phone, secret=False):
    return u'-'.join([
        phone[:3], phone[3:-4] if not secret else 'X' * len(phone[3:-4]),
        phone[-4:]])


def format_json(d, indent=4, sort_keys=True):
    return json.dumps(d, indent=indent, sort_keys=sort_keys)


def format_xml(xml_string):
    xml = minidom.parseString(xml_string)
    return xml.toprettyxml()
