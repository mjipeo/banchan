import datetime
import math
import time

try:
    from dateutil.parser import parse
except ImportError:
    # FIXME: Implement
    pass


def date_range(start, end):
    for i in xrange(int((end - start).days + 1)):
        yield start + datetime.timedelta(days=i)

# For consistency with Python standard library naming
daterange = date_range

parse_dt = parse


def week_of_month(date):
    return (date.day - 1) // 7 + 1


parse_dt = parse


def parse_date(val, format_=None):
    if format:
        return datetime.datetime.strptime(val, format_).date()
    else:
        return parse(val).date()


def convert_to_ts(dt):
    return time.mktime(dt.timetuple()) + dt.microsecond / 1000000.0


def get_date_by_weekday(year, month, weekday, index=0):
    dt = datetime.datetime(year, month, 1)
    dt += datetime.timedelta(days=(weekday - dt.weekday()) % 7)
    return (dt + datetime.timedelta(days=index*7)).date()


def split_date_range(start_date, end_date, count=None, days=None):
    if count is None and days is None:
        raise Exception('Either of `count` or `days` should be specified.')

    total_days = int((end_date - start_date).days) + 1
    days = days or math.ceil(float(total_days) / count)

    date = start_date
    while date <= end_date:
        local_start_date = date
        local_end_date = min(end_date, date + datetime.timedelta(days=days-1))
        yield local_start_date, local_end_date
        date = local_end_date + datetime.timedelta(days=1)
