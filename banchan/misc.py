def noop(*args, **kwargs):
    """No operation.

    Takes any arguments/keyword arguments and does nothing.

    """
    pass


class dummy(object):
    """
    Instances of this class can be used as an attribute container.
    """
    pass


class DummyContext(object):
    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        pass
