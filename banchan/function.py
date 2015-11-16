def only_once(fn):
    """Decorate the given function to be a no-op after it is called exactly
    once."""

    once = [fn]

    def go(*arg, **kw):
        if once:
            once_fn = once.pop()
            return once_fn(*arg, **kw)

    return go
