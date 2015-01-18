from decimal import Decimal as D, ROUND_UP
import re


_short_format_pattern = re.compile(r'(?P<number>[\d.]+)\s*(?P<suffix>[km])')


def parse_int(val, default=None):
    if isinstance(val, int):
        return val

    if not val:
        if default is not None:
            return default
        else:
            raise ValueError

    val = val.strip().lower()

    # Handle the case like `23.3k`
    match = _short_format_pattern.match(val)
    if match:
        groups = match.groupdict()
        number = float(groups['number'])
        suffix = groups['suffix']
        number *= 1000 if suffix == 'k' else 1000000
        return int(number)

    try:
        val = re.sub(r'[^\d,]', ' ', val)
        val = re.sub(r',', '', val)
        return int(val.split()[0])
    except Exception as e:
        if default is not None:
            return default
        else:
            raise(e)


def parse_float(val, default=None):
    if isinstance(val, float):
        return val

    if not val:
        if default is not None:
            return default
        else:
            raise ValueError

    val = val.strip().lower()

    # Handle the case like `23.3k`
    match = _short_format_pattern.match(val)
    if match:
        groups = match.groupdict()
        number = float(groups['number'])
        suffix = groups['suffix']
        number *= 1000 if suffix == 'k' else 1000000
        return int(number)

    try:
        val = re.sub(r'[^\d,.]', ' ', val)
        val = re.sub(r',', '', val)
        return float(val.split()[0])
    except Exception as e:
        if default is not None:
            return default
        else:
            raise(e)


def parse_decimal(value, decimal_places=2):
    return D(parse_float(value)).quantize(
        D('.' + ''.join(['0'] * decimal_places)),
        rounding=ROUND_UP)
