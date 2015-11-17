import re

from .cache import memoized


@memoized
def get_physical_memory_size():
    meminfo_path = '/proc/meminfo'
    info_pattern = re.compile(r'(?P<key>[^:]+):\s+(?P<value>\d+).*')

    try:
        with open(meminfo_path) as f:
            for line in f:
                match = info_pattern.match(line)
                if match:
                    info = match.groupdict()
                    if info['key'] == 'MemTotal':
                        return int(info['value']) * 1024
    except Exception as e:
        raise Exception('Something went wrong!: {0}'.format(e))


def cry(out=None, sepchr='=', seplen=49):  # pragma: no cover
    """Return stacktrace of all active threads,
    taken from https://gist.github.com/737056."""
    import threading

    out = WhateverIO() if out is None else out
    P = partial(print, file=out)

    # get a map of threads by their ID so we can print their names
    # during the traceback dump
    tmap = {t.ident: t for t in threading.enumerate()}

    sep = sepchr * seplen
    for tid, frame in items(sys._current_frames()):
        thread = tmap.get(tid)
        if not thread:
            # skip old junk (left-overs from a fork)
            continue
        P('{0.name}'.format(thread))
        P(sep)
        traceback.print_stack(frame, file=out)
        P(sep)
        P('LOCAL VARIABLES')
        P(sep)
        pprint(frame.f_locals, stream=out)
        P('\n')
    return out.getvalue()


def abort(msg):
    """
    Abort execution, print ``msg`` to stderr and exit with error status (1.)

    This function currently makes use of `SystemExit`_ in a manner that is
    similar to `sys.exit`_ (but which skips the automatic printing to stderr,
    allowing us to more tightly control it via settings).

    Therefore, it's possible to detect and recover from inner calls to `abort`
    by using ``except SystemExit`` or similar.

    .. _sys.exit: http://docs.python.org/library/sys.html#sys.exit
    .. _SystemExit: http://docs.python.org/library/exceptions.html#exceptions.SystemExit
    """
    from fabric.state import output, env
    if not env.colorize_errors:
        red  = lambda x: x
    else:
        from colors import red

    if output.aborts:
        sys.stderr.write(red("\nFatal error: %s\n" % _encode(msg, sys.stderr)))
        sys.stderr.write(red("\nAborting.\n"))

    if env.abort_exception:
        raise env.abort_exception(msg)
    else:
        # See issue #1318 for details on the below; it lets us construct a
        # valid, useful SystemExit while sidestepping the automatic stderr
        # print (which would otherwise duplicate with the above in a
        # non-controllable fashion).
        e = SystemExit(1)
        e.message = msg
        raise e


def warn(msg):
    """
    Print warning message, but do not abort execution.

    This function honors Fabric's :doc:`output controls
    <../../usage/output_controls>` and will print the given ``msg`` to stderr,
    provided that the ``warnings`` output level (which is active by default) is
    turned on.
    """
    from fabric.state import output, env

    if not env.colorize_errors:
        magenta = lambda x: x
    else:
        from colors import magenta

    if output.warnings:
        msg = _encode(msg, sys.stderr)
        sys.stderr.write(magenta("\nWarning: %s\n\n" % msg))


def set_owner_process(uid, gid):
    """ set user and group of workers processes """
    if gid:
        # versions of python < 2.6.2 don't manage unsigned int for
        # groups like on osx or fedora
        gid = abs(gid) & 0x7FFFFFFF
        os.setgid(gid)
    if uid:
        os.setuid(uid)


def chown(path, uid, gid):
    gid = abs(gid) & 0x7FFFFFFF  # see note above.
    os.chown(path, uid, gid)


def get_maxfd():
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if (maxfd == resource.RLIM_INFINITY):
        maxfd = MAXFD
    return maxfd


def getcwd():
    # get current path, try to use PWD env first
    try:
        a = os.stat(os.environ['PWD'])
        b = os.stat(os.getcwd())
        if a.st_ino == b.st_ino and a.st_dev == b.st_dev:
            cwd = os.environ['PWD']
        else:
            cwd = os.getcwd()
    except:
        cwd = os.getcwd()
    return cwd


def emergency_dump_state(state, open_file=open, dump=None, stderr=None):
    from pprint import pformat
    from tempfile import mktemp
    stderr = sys.stderr if stderr is None else stderr

    if dump is None:
        import pickle
        dump = pickle.dump
    persist = mktemp()
    print('EMERGENCY DUMP STATE TO FILE -> {0} <-'.format(persist), ## noqa
          file=stderr)
    fh = open_file(persist, 'w')
    try:
        try:
            dump(state, fh, protocol=0)
        except Exception as exc:
            print(  # noqa
                'Cannot pickle state: {0!r}. Fallback to pformat.'.format(exc),
                file=stderr,
            )
            fh.write(default_encode(pformat(state)))
    finally:
        fh.flush()
        fh.close()
    return persist


def get_filesystem_encoding():
    """
    Returns the filesystem encoding that should be used. Note that this is
    different from the Python understanding of the filesystem encoding which
    might be deeply flawed. Do not use this value against Python's unicode APIs
    because it might be different. See :ref:`filesystem-encoding` for the exact
    behavior.

    The concept of a filesystem encoding in generally is not something you
    should rely on. As such if you ever need to use this function except for
    writing wrapper code reconsider.
    """
    global _warned_about_filesystem_encoding
    rv = sys.getfilesystemencoding()
    if has_likely_buggy_unicode_filesystem and not rv \
       or _is_ascii_encoding(rv):
        if not _warned_about_filesystem_encoding:
            warnings.warn(
                'Detected a misconfigured UNIX filesystem: Will use UTF-8 as '
                'filesystem encoding instead of {!r}'.format(rv),
                BrokenFilesystemWarning)
            _warned_about_filesystem_encoding = True
        return 'utf-8'
    return rv


def gen_unique_id():
    """Generate a unique id, having - hopefully - a very small chance of
    collission.
    For now this is provided by :func:`uuid.uuid4`.
    """
    # Workaround for http://bugs.python.org/issue4607
    if ctypes and _uuid_generate_random:
        buffer = ctypes.create_string_buffer(16)
        _uuid_generate_random(buffer)
        return str(UUID(bytes=buffer.raw))
    return str(uuid4())


##


def get_platform():
    ''' what's the platform?  example: Linux is a platform. '''
    return platform.system()

def get_distribution():
    ''' return the distribution name '''
    if platform.system() == 'Linux':
        try:
            supported_dists = platform._supported_dists + ('arch',)
            distribution = platform.linux_distribution(supported_dists=supported_dists)[0].capitalize()
            if not distribution and os.path.isfile('/etc/system-release'):
                distribution = platform.linux_distribution(supported_dists=['system'])[0].capitalize()
                if 'Amazon' in distribution:
                    distribution = 'Amazon'
                else:
                    distribution = 'OtherLinux'
        except:
            # FIXME: MethodMissing, I assume?
            distribution = platform.dist()[0].capitalize()
    else:
        distribution = None
    return distribution

def get_distribution_version():
    ''' return the distribution version '''
    if platform.system() == 'Linux':
        try:
            distribution_version = platform.linux_distribution()[1]
            if not distribution_version and os.path.isfile('/etc/system-release'):
                distribution_version = platform.linux_distribution(supported_dists=['system'])[1]
        except:
            # FIXME: MethodMissing, I assume?
            distribution_version = platform.dist()[1]
    else:
        distribution_version = None
    return distribution_version

def load_platform_subclass(cls, *args, **kwargs):
    '''
    used by modules like User to have different implementations based on detected platform.  See User
    module for an example.
    '''

    this_platform = get_platform()
    distribution = get_distribution()
    subclass = None

    # get the most specific superclass for this platform
    if distribution is not None:
        for sc in cls.__subclasses__():
            if sc.distribution is not None and sc.distribution == distribution and sc.platform == this_platform:
                subclass = sc
    if subclass is None:
        for sc in cls.__subclasses__():
            if sc.platform == this_platform and sc.distribution is None:
                subclass = sc
    if subclass is None:
        subclass = cls

    return super(cls, subclass).__new__(subclass)


##


class Signals(object):
    """Convenience interface to :mod:`signals`.

    If the requested signal is not supported on the current platform,
    the operation will be ignored.

    **Examples**:

    .. code-block:: pycon

        >>> from celery.platforms import signals

        >>> from proj.handlers import my_handler
        >>> signals['INT'] = my_handler

        >>> signals['INT']
        my_handler

        >>> signals.supported('INT')
        True

        >>> signals.signum('INT')
        2

        >>> signals.ignore('USR1')
        >>> signals['USR1'] == signals.ignored
        True

        >>> signals.reset('USR1')
        >>> signals['USR1'] == signals.default
        True

        >>> from proj.handlers import exit_handler, hup_handler
        >>> signals.update(INT=exit_handler,
        ...                TERM=exit_handler,
        ...                HUP=hup_handler)

    """

    ignored = _signal.SIG_IGN
    default = _signal.SIG_DFL

    if hasattr(_signal, 'setitimer'):

        def arm_alarm(self, seconds):
            _signal.setitimer(_signal.ITIMER_REAL, seconds)
    else:  # pragma: no cover
        try:
            from itimer import alarm as _itimer_alarm  # noqa
        except ImportError:

            def arm_alarm(self, seconds):  # noqa
                _signal.alarm(math.ceil(seconds))
        else:  # pragma: no cover

            def arm_alarm(self, seconds):      # noqa
                return _itimer_alarm(seconds)  # noqa

    def reset_alarm(self):
        return _signal.alarm(0)

    def supported(self, signal_name):
        """Return true value if ``signal_name`` exists on this platform."""
        try:
            return self.signum(signal_name)
        except AttributeError:
            pass

    def signum(self, signal_name):
        """Get signal number from signal name."""
        if isinstance(signal_name, numbers.Integral):
            return signal_name
        if not isinstance(signal_name, string_t) \
                or not signal_name.isupper():
            raise TypeError('signal name must be uppercase string.')
        if not signal_name.startswith('SIG'):
            signal_name = 'SIG' + signal_name
        return getattr(_signal, signal_name)

    def reset(self, *signal_names):
        """Reset signals to the default signal handler.

        Does nothing if the platform doesn't support signals,
        or the specified signal in particular.

        """
        self.update((sig, self.default) for sig in signal_names)

    def ignore(self, *signal_names):
        """Ignore signal using :const:`SIG_IGN`.

        Does nothing if the platform doesn't support signals,
        or the specified signal in particular.

        """
        self.update((sig, self.ignored) for sig in signal_names)

    def __getitem__(self, signal_name):
        return _signal.getsignal(self.signum(signal_name))

    def __setitem__(self, signal_name, handler):
        """Install signal handler.

        Does nothing if the current platform doesn't support signals,
        or the specified signal in particular.

        """
        try:
            _signal.signal(self.signum(signal_name), handler)
        except (AttributeError, ValueError):
            pass

    def update(self, _d_=None, **sigmap):
        """Set signal handlers from a mapping."""
        for signal_name, handler in items(dict(_d_ or {}, **sigmap)):
            self[signal_name] = handler

signals = Signals()
get_signal = signals.signum                   # compat
install_signal_handler = signals.__setitem__  # compat
reset_signal = signals.reset                  # compat
ignore_signal = signals.ignore                # compat

##

# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

import errno
import os
import tempfile


class Pidfile(object):
    """\
    Manage a PID file. If a specific name is provided
    it and '"%s.oldpid" % name' will be used. Otherwise
    we create a temp file using os.mkstemp.
    """

    def __init__(self, fname):
        self.fname = fname
        self.pid = None

    def create(self, pid):
        oldpid = self.validate()
        if oldpid:
            if oldpid == os.getpid():
                return
            msg = "Already running on PID %s (or pid file '%s' is stale)"
            raise RuntimeError(msg % (oldpid, self.fname))

        self.pid = pid

        # Write pidfile
        fdir = os.path.dirname(self.fname)
        if fdir and not os.path.isdir(fdir):
            raise RuntimeError("%s doesn't exist. Can't create pidfile." % fdir)
        fd, fname = tempfile.mkstemp(dir=fdir)
        os.write(fd, ("%s\n" % self.pid).encode('utf-8'))
        if self.fname:
            os.rename(fname, self.fname)
        else:
            self.fname = fname
        os.close(fd)

        # set permissions to -rw-r--r--
        os.chmod(self.fname, 420)

    def rename(self, path):
        self.unlink()
        self.fname = path
        self.create(self.pid)

    def unlink(self):
        """ delete pidfile"""
        try:
            with open(self.fname, "r") as f:
                pid1 = int(f.read() or 0)

            if pid1 == self.pid:
                os.unlink(self.fname)
        except:
            pass

    def validate(self):
        """ Validate pidfile and make it stale if needed"""
        if not self.fname:
            return
        try:
            with open(self.fname, "r") as f:
                try:
                    wpid = int(f.read())
                except ValueError:
                    return

                try:
                    os.kill(wpid, 0)
                    return wpid
                except OSError as e:
                    if e.args[0] == errno.ESRCH:
                        return
                    raise
        except IOError as e:
            if e.args[0] == errno.ENOENT:
                return
            raise
