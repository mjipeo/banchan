def curry(_curried_func, *args, **kwargs):
    # You can't trivially replace this with `functools.partial` because this
    # binds to classes and returns bound instances, whereas functools.partial
    # (on CPython) is a type and its instances don't bind.
    def _curried(*moreargs, **morekwargs):
        return _curried_func(*(args + moreargs), **dict(kwargs, **morekwargs))
    return _curried
