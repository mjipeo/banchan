import hashlib


def sha1(value):
    return hashlib.sha1(value).hexdigest()
