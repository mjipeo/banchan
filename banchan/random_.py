import hashlib
import os
import random
import string
import time

from .hash import sha1


class Dice(object):
    """Simple dice class to randomly choose one value from a list based on weight.

    It's basically same as random.choice, but you can specify the odds for each element.
    """

    def __init__(self, *odds):
        if odds and (not odds[0] or isinstance(odds[0][0], (list, tuple))):
            odds = odds[0]
        self._odds = dict(odds)

    def __unicode__(self):
        return u'{0}({1})'.format(self.__class__.__name__, self._odds)

    def __repr__(self):
        return self.__unicode__()

    def __call__(self):
        return self.roll()

    def has(self, value):
        return value in self._odds

    def get_odd(self, value):
        return self._odds.get(value)

    def remove_odd(self, value):
        return self._odds.pop(value, None)

    def keys(self):
        return self._odds.keys()

    def add_odd(self, value, odd=1):
        assert odd >= 0, 'Should be bigger than zero'
        self._odds[value] = odd
        return self

    def add_odds(self, odds):
        for odd in odds:
            self.add_odd(*odd)
        return self

    def set_odd(self, value, odd):
        self.add_odd(value, odd)
        return self

    def roll(self):
        assert len(self._odds) > 0, 'No odd to roll'

        _random_seed()

        total = sum(odd for odd in self._odds.itervalues())
        pick = random.uniform(0, total)
        upto = 0.0

        for value, odd in self._odds.iteritems():
            if upto + odd > pick:
                return value
            upto += odd

        assert False, 'Shouldn\'t get here'


class CacheDice(Dice):
    """Periodically cache the randomly selected value."""

    def __init__(self, timeout, *odds):
        super(CacheDice, self).__init__(*odds)
        self._timeout = timeout
        self._last_rolled_at = None
        self._cache = None

    @property
    def timeout(self):
        return self._timeout

    @property
    def elapsed(self):
        if self._last_rolled_at is None:
            return None
        return time.time() - self._last_rolled_at

    def do_roll(self):
        self._last_rolled_at = time.time()
        return super(CacheDice, self).roll()

    def roll(self):
        if self._cache is None or self.elapsed is None \
                or self.elapsed >= self.timeout:
            self._cache = self.do_roll()
        return self._cache


class FuzzyCacheDice(CacheDice):
    """Randomize the timeout of CacheDice."""

    def __init__(self, timeout, *odds):
        super(FuzzyCacheDice, self).__init__(timeout, *odds)
        self._current_timeout = self._get_next_timeout()

    @property
    def timeout(self):
        return self._current_timeout

    def _get_next_timeout(self):
        return self._timeout() if hasattr(self._timeout, '__call__') else \
               self._timeout

    def do_roll(self):
        self._current_timeout = self._get_next_timeout()
        return super(FuzzyCacheDice, self).do_roll()


def _random_seed():
    try:
        random.seed(os.urandom(100))
    except OSError:
        pass

def random_hash():
    return sha1(os.urandom(100))

def random_string(length):
    _random_seed()
    return ''.join(random.choice(string.ascii_lowercase + string.digits)
                   for x in range(length))

def random_int(start, end):
    _random_seed()
    return random.randint(start, end)

def random_int_inverse(size):
    d = Dice()
    for i in range(size):
        c = i + 1
        d.add_odd(c, float(size) / c)
    return d.roll()

def random_gauss_int(start, end):
    _random_seed()
    count, n = 0, end - start
    for i in xrange(n):
        if random.random() < 0.5:
            count += 1
    return start + count

def random_gauss_int_inverse(size):
    return int(abs(random_gauss(size) - size))

def random_gauss(mu, std=None):
    std = std or float(mu) / 4
    return random.gauss(mu, std)

def random_digit():
    return random_int(0, 9)

def shuffled(iterable):
    iterable = list(iterable)
    random.shuffle(iterable)
    return iterable

def weighted_choice(odds):
    return Dice(odds).roll()
