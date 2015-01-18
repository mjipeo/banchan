from collections import Counter
import time

from .log import LoggableMixin


class _ProfilerContext(object):
    def __init__(self, profiler, key):
        self._profiler = profiler
        self._key = key

    def __enter__(self):
        self._profiler.start(self._key)

    def __exit__(self, type, value, traceback):
        self._profiler.finish(self._key)


class Profiler(LoggableMixin):
    now = staticmethod(time.time)

    def __init__(self):
        super(Profiler, self).__init__()
        self._started_times = {}
        self._elapsed_total = Counter()
        self._elapsed_average = Counter()
        self._counts = Counter()

    @property
    def elapsed_total(self):
        return self._elapsed_total

    @property
    def elapsed_average(self):
        return self._elapsed_average

    @property
    def counts(self):
        return self._counts

    def update(self, profiler):
        self.__dict__.update(profiler.__dict__)

    def measure(self, key):
        return _ProfilerContext(self, key)

    def start(self, key=None):
        self._counts.setdefault(key, 0)
        self._elapsed_total.setdefault(key, 0.0)
        self._started_times[key] = self.now()

    def finish(self, key=None):
        local = self.now() - self._started_times[key]
        self._elapsed_total[key] += local
        self._counts[key] += 1
        self._update(key)
        return local

    def report(self):
        print_func = self.debug
        print_line = lambda: print_func('=' * sum(sizes))

        cols = ['key', 'count', 'average', 'total']
        sizes = [40, 10, 15, 15]

        print_line()
        print_func(u' '.join([
            col.ljust(sizes[i])for i, col in enumerate(cols)]))
        print_line()

        for key in sorted(self._counts.keys()):
            print_func(u' '.join([
                ('{0:.6}' if isinstance(val, float)
                 else '{0}').format(val).ljust(sizes[i])
                for i, val in enumerate([
                    key, self._counts[key], self._elapsed_average[key],
                    self._elapsed_total[key]])]))

        print_line()

    def _update(self, key):
        self._elapsed_average[key] = (
            self._elapsed_total[key] / self._counts[key]
            if self._counts[key] > 0 else 0)
