import cPickle as pickle


class Pickable(object):
    def get_unpicklables(self):
        return {}

    def __getstate__(self):
        unpicklables = self.get_unpicklables()
        state = dict([
            (k, (v if k not in unpicklables else unpicklables[k]))
            for k, v in self.__dict__.iteritems()
        ])
        return state


def dump_obj(obj):
    return pickle.dumps(obj)


def load_obj(dumped):
    return pickle.loads(str(dumped))
