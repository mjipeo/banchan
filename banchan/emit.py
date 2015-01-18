from collections import defaultdict
import string

import datrie


class EmitterMixin(object):
    # TODO: Non-prefix version with datrie

    def __init__(self, *args, **kwargs):
        super(EmitterMixin, self).__init__(*args, **kwargs)
        self._callbacks = datrie.Trie(string.printable)

    def on(self, event, callback):
        event = unicode(event)
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def emit(self, event, *args, **kwargs):
        event = unicode(event)
        for callbacks in self._callbacks.iter_prefix_values(event):
            for callback in callbacks:
                callback(*args, **kwargs)
