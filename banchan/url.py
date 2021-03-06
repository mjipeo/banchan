import urllib
import urlparse


def get_url_path(url):
    return urlparse.urlparse(url).path


def get_url_host(url):
    return urlparse.urlparse(url).netloc


def strip_trailing_slashes(url):
    return url.rstrip('/')


def add_url_params(url, data):
    parsed = list(urlparse.urlparse(url))
    params = dict(urlparse.parse_qsl(parsed[4]))
    params.update(data)
    parsed[4] = urllib.urlencode(params)
    return urlparse.urlunparse(parsed)


def add_url_param(url, key, value):
    return add_url_params(url, {key: value})


def remove_url_params(url, *keys):
    parsed = list(urlparse.urlparse(url))
    params = dict(urlparse.parse_qsl(parsed[4]))
    for key in keys:
        try:
            del params[key]
        except Exception:
            pass
    parsed[4] = urllib.urlencode(params)
    return urlparse.urlunparse(parsed)


remove_url_param = remove_url_params


def get_url_param(url, key):
    parsed = list(urlparse.urlparse(url))
    params = dict(urlparse.parse_qsl(parsed[4]))
    return urllib.unquote(params.get(key, ''))


def absolutify(url, host, scheme='http'):
    return urlparse.urljoin('{scheme}://{host}'.format(
        scheme=scheme, host=host), url)


def ensure_protocol(url, default='http'):
    return urlparse.urljoin('{0}://'.format(default), url)


def replace_query_param(url, key, val):
    """
    Given a URL and a key/val pair, set or replace an item in the query
    parameters of the URL, and return the new URL.
    """
    (scheme, netloc, path, query, fragment) = urlparse.urlsplit(url)
    query_dict = urlparse.parse_qs(query)
    query_dict[key] = [val]
    query = urlparse.urlencode(sorted(list(query_dict.items())), doseq=True)
    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))
