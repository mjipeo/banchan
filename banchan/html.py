import re


def strip_tags(s):
    return re.sub(r'<[^>]*?>', '', s)
