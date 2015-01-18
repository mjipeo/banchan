from math import radians, cos, sin, asin, sqrt
import logging
import re
import urllib2

try:
    from rtree.index import Rtree
except ImportError:
    pass


logger = logging.getLogger(__name__)


PATTERN_COUNTRY = re.compile(r'Country: (.+)\n')
PATTERN_CITY = re.compile('City: (.+)\n')


def get_location_info(ip):
    """Get an estimated location info give IP address."""
    cache = getattr(get_location_info, '_cache', {})
    if ip in cache:
        return cache[ip]

    url = 'http://api.hostip.info/get_html.php?ip={0}'.format(ip)
    country, city = '', ''
    try:
        res = urllib2.urlopen(url).read()
        m = PATTERN_COUNTRY.search(res)
        if m:
            country = m.group(1)
        m = PATTERN_CITY.search(res)
        if m:
            city = m.group(1)
    except Exception, e:
        logger.error("Failed to the location of %s : %s" % (ip, e))
    finally:
        if country.find('Unknown') >= 0:
            country = ''
        if city.find('Unknown') >= 0:
            city = ''

        cache[ip] = (country, city)

        return country, city


def haversine(*p):
    """Calculate the great circle distance between two points on the earth
    (specified in decimal degrees)
    """
    if len(p) == 1:
        p1, p2 = p[0]
    else:
        p1, p2 = p

    lon1, lat1 = p1
    lon2, lat2 = p2

    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))

    # 6367 km is the radius of the Earth
    km = 6367 * c
    return km * 1000


# Alias
distance = haversine


def move(source, distance, direction=(1, 1)):
    pseudo_destination = map(sum, zip(source, direction))
    pseudo_distance = haversine(source, pseudo_destination)
    scale = float(distance) / pseudo_distance
    offset = map(lambda x: x * scale, direction)
    return map(sum, zip(source, offset))


class Rtree2D(object):
    """Wrapper of `rtree.Index` for supporting friendly 2d operations.

    Also forces the uniqueness of the `id` parameter, which is different from
    the rtree module's behavior.
    """

    def __init__(self):
        self._index = Rtree()
        self._locations = {}

    @staticmethod
    def to_coords(location):
        return (location[0], location[1], location[0], location[1])

    def keys(self):
        return self._locations.keys()

    def get(self, id, objects=False):
        return self._locations.get(id)

    def set(self, id, location, obj=None):
        # Clean up previous value first if any
        old = self._locations.get(id)
        if old is not None:
            self._index.delete(id, self.to_coords(old))

        self._locations[id] = location
        self._index.insert(id, self.to_coords(location), obj=obj)

    def remove(self, id):
        self._index.delete(id, self.to_coords(self._locations[id]))
        del self._locations[id]

    def nearest(self, location, count=1, objects=False, max_distance=None):
        ids = self._index.nearest(self.to_coords(location), num_results=count,
                                  objects=objects)
        if max_distance is not None:
            ids = [id_ for id_ in ids
                   if distance(self._locations[id_], location) <= max_distance]
        return ids
