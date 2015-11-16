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


def format_number_like_a_boss(number, decimal_sep, decimal_pos=None,
                              grouping=0, thousand_sep='',
                              force_grouping=False):
    """
    Gets a number (as a number or string), and returns it as a string,
    using formats defined as arguments:

    * decimal_sep: Decimal separator symbol (for example ".")
    * decimal_pos: Number of decimal positions
    * grouping: Number of digits in every group limited by thousand separator
    * thousand_sep: Thousand separator symbol (for example ",")
    """
    use_grouping = settings.USE_L10N and settings.USE_THOUSAND_SEPARATOR
    use_grouping = use_grouping or force_grouping
    use_grouping = use_grouping and grouping > 0
    # Make the common case fast
    if isinstance(number, int) and not use_grouping and not decimal_pos:
        return mark_safe(six.text_type(number))
    # sign
    sign = ''
    if isinstance(number, Decimal):
        str_number = '{:f}'.format(number)
    else:
        str_number = six.text_type(number)
    if str_number[0] == '-':
        sign = '-'
        str_number = str_number[1:]
    # decimal part
    if '.' in str_number:
        int_part, dec_part = str_number.split('.')
        if decimal_pos is not None:
            dec_part = dec_part[:decimal_pos]
    else:
        int_part, dec_part = str_number, ''
    if decimal_pos is not None:
        dec_part = dec_part + ('0' * (decimal_pos - len(dec_part)))
    if dec_part:
        dec_part = decimal_sep + dec_part
    # grouping
    if use_grouping:
        int_part_gd = ''
        for cnt, digit in enumerate(int_part[::-1]):
            if cnt and not cnt % grouping:
                int_part_gd += thousand_sep[::-1]
            int_part_gd += digit
        int_part = int_part_gd[::-1]
    return sign + int_part + dec_part


def format_size(bytes):
    if bytes > 1000 * 1000:
        return '%.1fMB' % (bytes / 1000.0 / 1000)
    elif bytes > 10 * 1000:
        return '%ikB' % (bytes / 1000)
    elif bytes > 1000:
        return '%.1fkB' % (bytes / 1000.0)
    else:
        return '%ibytes' % bytes
