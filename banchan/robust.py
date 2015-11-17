import time
import math


# Retry decorator with exponential backoff
def retry(tries, delay=3, backoff=2):
  '''Retries a function or method until it returns True.

    https://wiki.python.org/moin/PythonDecoratorLibrary#Retry

  delay sets the initial delay in seconds, and backoff sets the factor by which
  the delay should lengthen after each failure. backoff must be greater than 1,
  or else it isn't really a backoff. tries must be at least 0, and delay
  greater than 0.'''

  if backoff <= 1:
    raise ValueError("backoff must be greater than 1")

  tries = math.floor(tries)
  if tries < 0:
    raise ValueError("tries must be 0 or greater")

  if delay <= 0:
    raise ValueError("delay must be greater than 0")

  def deco_retry(f):
    def f_retry(*args, **kwargs):
      mtries, mdelay = tries, delay # make mutable

      rv = f(*args, **kwargs) # first attempt
      while mtries > 0:
        if rv is True: # Done on success
          return True

        mtries -= 1      # consume an attempt
        time.sleep(mdelay) # wait...
        mdelay *= backoff  # make future wait longer

        rv = f(*args, **kwargs) # Try again

      return False # Ran out of tries :-(

    return f_retry # true decorator -> decorated function
  return deco_retry  # @retry(arg[, ...]) -> true decorator


#####

# https://gist.github.com/n1ywb/2570004

#!/usr/bin/env python
#
# Copyright 2012 by Jeff Laughlin Consulting LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import sys
from time import sleep


def example_exc_handler(tries_remaining, exception, delay):
    """Example exception handler; prints a warning to stderr.

    tries_remaining: The number of tries remaining.
    exception: The exception instance which was raised.
    """
    print >> sys.stderr, "Caught '%s', %d tries remaining, sleeping for %s seconds" % (exception, tries_remaining, delay)


def retries(max_tries, delay=1, backoff=2, exceptions=(Exception,), hook=None):
    """Function decorator implementing retrying logic.

    delay: Sleep this many seconds * backoff * try number after failure
    backoff: Multiply delay by this factor after each failure
    exceptions: A tuple of exception classes; default (Exception,)
    hook: A function with the signature myhook(tries_remaining, exception);
          default None

    The decorator will call the function up to max_tries times if it raises
    an exception.

    By default it catches instances of the Exception class and subclasses.
    This will recover after all but the most fatal errors. You may specify a
    custom tuple of exception classes with the 'exceptions' argument; the
    function will only be retried if it raises one of the specified
    exceptions.

    Additionally you may specify a hook function which will be called prior
    to retrying with the number of remaining tries and the exception instance;
    see given example. This is primarily intended to give the opportunity to
    log the failure. Hook is not called after failure if no retries remain.
    """
    def dec(func):
        def f2(*args, **kwargs):
            mydelay = delay
            tries = range(max_tries)
            tries.reverse()
            for tries_remaining in tries:
                try:
                   return func(*args, **kwargs)
                except exceptions as e:
                    if tries_remaining > 0:
                        if hook is not None:
                            hook(tries_remaining, e, mydelay)
                        sleep(mydelay)
                        mydelay = mydelay * backoff
                    else:
                        raise
                else:
                    break
        return f2
    return dec

# TEST

#!/usr/bin/env python
#
# Copyright 2012 by Jeff Laughlin Consulting LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from retry import retries, example_exc_handler
import nose.tools
from nose.tools import *

class MyException(Exception):
    pass

n = 0
@retries(3, hook=example_exc_handler)
def retry_me():
    global n
    n += 1
    raise MyException('Foobar')

def test_retries():
    try:
        retry_me()
    except MyException, e:
        pass
    else:
        raise Exception("Failure to raise MyException")
    eq_(n, 3)

@retries(4, hook=example_exc_handler)
def retry_me2():
    raise BaseException()

def test_retries2():
    assert_raises(BaseException, retry_me2)


def retry_over_time(fun, catch, args=[], kwargs={}, errback=None,
                    max_retries=None, interval_start=2, interval_step=2,
                    interval_max=30, callback=None):
    """Retry the function over and over until max retries is exceeded.

    For each retry we sleep a for a while before we try again, this interval
    is increased for every retry until the max seconds is reached.

    :param fun: The function to try
    :param catch: Exceptions to catch, can be either tuple or a single
        exception class.
    :keyword args: Positional arguments passed on to the function.
    :keyword kwargs: Keyword arguments passed on to the function.
    :keyword errback: Callback for when an exception in ``catch`` is raised.
        The callback must take three arguments: ``exc``, ``interval_range`` and
        ``retries``, where ``exc`` is the exception instance, ``interval_range``
        is an iterator which return the time in seconds to sleep next, and
        ``retries`` is the number of previous retries.
    :keyword max_retries: Maximum number of retries before we give up.
        If this is not set, we will retry forever.
    :keyword interval_start: How long (in seconds) we start sleeping between
        retries.
    :keyword interval_step: By how much the interval is increased for each
        retry.
    :keyword interval_max: Maximum number of seconds to sleep between retries.

    """
    retries = 0
    interval_range = fxrange(interval_start,
                             interval_max + interval_start,
                             interval_step, repeatlast=True)
    for retries in count():
        try:
            return fun(*args, **kwargs)
        except catch as exc:
            if max_retries and retries >= max_retries:
                raise
            if callback:
                callback()
            tts = float(errback(exc, interval_range, retries) if errback
                        else next(interval_range))
            if tts:
                for _ in range(int(tts)):
                    if callback:
                        callback()
                    sleep(1.0)
                # sleep remainder after int truncation above.
                sleep(abs(int(tts) - tts))


##


def retry_over_time(fun, catch, args=[], kwargs={}, errback=None,
        max_retries=None, interval_start=2, interval_step=2, interval_max=30):
    """Retry the function over and over until max retries is exceeded.
    For each retry we sleep a for a while before we try again, this interval
    is increased for every retry until the max seconds is reached.
    :param fun: The function to try
    :param catch: Exceptions to catch, can be either tuple or a single
        exception class.
    :keyword args: Positional arguments passed on to the function.
    :keyword kwargs: Keyword arguments passed on to the function.
    :keyword errback: Callback for when an exception in ``catch`` is raised.
        The callback must take two arguments: ``exc`` and ``interval``, where
        ``exc`` is the exception instance, and ``interval`` is the time in
        seconds to sleep next..
    :keyword max_retries: Maximum number of retries before we give up.
        If this is not set, we will retry forever.
    :keyword interval_start: How long (in seconds) we start sleeping between
        retries.
    :keyword interval_step: By how much the interval is increased for each
        retry.
    :keyword interval_max: Maximum number of seconds to sleep between retries.
    """
    retries = 0
    interval_range = xrange(interval_start,
                            interval_max + interval_start,
                            interval_step)

    for retries, interval in enumerate(repeatlast(interval_range)):
        try:
            retval = fun(*args, **kwargs)
        except catch, exc:
            if max_retries and retries > max_retries:
                raise
            if errback:
                errback(exc, interval)
            sleep(interval)
        else:
            return retval
