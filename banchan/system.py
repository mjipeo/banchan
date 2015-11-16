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
