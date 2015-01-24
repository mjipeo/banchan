import datetime

try:
    import simplejson as json
except ImportError:
    import json


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'for_json'):
            return obj.for_json()
        elif isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        return super(Encoder, self).default(obj)


# TODO: Implement decoder for datetime objects


def json_dumps(obj, *args, **kwargs):
    return json.dumps(obj, cls=Encoder, *args, **kwargs)

dumps = json_dumps
loads = json.loads
