import re

from .log import LogMixin
from .url import get_url_path


class RouteMixin(LogMixin):
    routes = ()

    def __init__(self):
        super(RouteMixin, self).__init__()
        self._compiled_routes = None

    @staticmethod
    def get_url_path(url):
        return get_url_path(url)

    @property
    def compiled_routes(self):
        if self._compiled_routes is None:
            self._compiled_routes = [
                (re.compile(pattern), handler)
                for pattern, handler in self.routes]
        return self._compiled_routes

    def _get_route(self, url):
        path = self.get_url_path(url)
        for pattern, handler in self.compiled_routes:
            match = pattern.match(path)
            if match:
                return handler, match.groupdict()
        return None, None

    def is_routable(self, url):
        return bool(self._get_route(url)[0])

    def route(self, url, **kwargs):
        handler, groups = self._get_route(url)
        if not handler:
            self.error('Not routable: {0}'.format(url))
            return
        kwargs.update(groups)
        self.debug('Routing {0}'.format(url))
        return getattr(self, handler)(url, **kwargs)
