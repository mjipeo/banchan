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


def host_is_ipv6(hostname):
    """
    Detect (naively) if the hostname is an IPV6 host.
    Return a boolean.
    """
    # empty strings or anything that is not a string is automatically not an
    # IPV6 address
    if not hostname or not isinstance(hostname, str):
        return False

    if hostname.startswith('['):
        return True

    if len(hostname.split(':')) > 2:
        return True

    # Anything else that doesn't start with brackets or doesn't have more than
    # one ':' should not be an IPV6 address. This is very naive but the rest of
    # the connection chain should error accordingly for typos or ill formed
    # addresses
    return False


def parse_host(hostname):
    """
    Given a hostname that may have a port name, ensure that the port is trimmed
    returning only the host, including hostnames that are IPV6 and may include
    brackets.
    """
    # ensure that hostname does not have any whitespaces
    hostname = hostname.strip()

    if host_is_ipv6(hostname):
        return hostname.split(']:', 1)[0].strip('[]')
    else:
        return hostname.split(':', 1)[0]


def is_ipv6(addr):
    try:
        socket.inet_pton(socket.AF_INET6, addr)
    except socket.error:  # not a valid address
        return False
    except ValueError:  # ipv6 not supported on this platform
        return False
    return True


def parse_address(netloc, default_port=8000):
    if netloc.startswith("unix://"):
        return netloc.split("unix://")[1]

    if netloc.startswith("unix:"):
        return netloc.split("unix:")[1]

    if netloc.startswith("tcp://"):
        netloc = netloc.split("tcp://")[1]

    # get host
    if '[' in netloc and ']' in netloc:
        host = netloc.split(']')[0][1:].lower()
    elif ':' in netloc:
        host = netloc.split(':')[0].lower()
    elif netloc == "":
        host = "0.0.0.0"
    else:
        host = netloc.lower()

    #get port
    netloc = netloc.split(']')[-1]
    if ":" in netloc:
        port = netloc.split(':', 1)[1]
        if not port.isdigit():
            raise RuntimeError("%r is not a valid port number." % port)
        port = int(port)
    else:
        port = default_port
    return (host, port)


def is_ipv4_address(string_ip):
    try:
        socket.inet_aton(string_ip)
    except socket.error:
        return False
    return True


def split_host_and_port(netloc):
    """Returns ``(host, port)`` tuple from ``netloc``.

    Returned ``port`` will be ``None`` if not present.

    .. versionadded:: 4.1
    """
    match = re.match(r'^(.+):(\d+)$', netloc)
    if match:
        host = match.group(1)
        port = int(match.group(2))
    else:
        host = netloc
        port = None
    return (host, port)


def is_valid_ip(ip):
    """Returns true if the given string is a well-formed IP address.

    Supports IPv4 and IPv6.
    """
    if not ip or '\x00' in ip:
        # getaddrinfo resolves empty strings to localhost, and truncates
        # on zero bytes.
        return False
    try:
        res = socket.getaddrinfo(ip, 0, socket.AF_UNSPEC,
                                 socket.SOCK_STREAM,
                                 0, socket.AI_NUMERICHOST)
        return bool(res)
    except socket.gaierror as e:
        if e.args[0] == socket.EAI_NONAME:
            return False
        raise
    return True
