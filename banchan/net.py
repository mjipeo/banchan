import requests

from django.conf import settings

from cache import Cacheable


def _get_public_ip():
    hosts = [
        'http://ipinfo.io/ip',
        'http://ip.42.pl/raw',
        'http://icanhazip.com/',
        'http://api.externalip.net/ip',
    ]

    def _fetch_ip(host):
        return requests.get(
            host, timeout=settings.IP_FETCH_TIMEOUT).text.strip()

    for host in hosts:
        try:
            return _fetch_ip(host)
        except Exception as e:
            continue

    return settings.DEFAULT_IP

get_public_ip = Cacheable(func=_get_public_ip, timeout=24*60*60)
