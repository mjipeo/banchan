class LockFailed(Exception):
    """Raised if a pidlock can't be acquired."""


class Pidfile(object):
    """Pidfile

    This is the type returned by :func:`create_pidlock`.

    TIP: Use the :func:`create_pidlock` function instead,
    which is more convenient and also removes stale pidfiles (when
    the process holding the lock is no longer running).

    """

    #: Path to the pid lock file.
    path = None

    def __init__(self, path):
        self.path = os.path.abspath(path)

    def acquire(self):
        """Acquire lock."""
        try:
            self.write_pid()
        except OSError as exc:
            reraise(LockFailed, LockFailed(str(exc)), sys.exc_info()[2])
        return self
    __enter__ = acquire

    def is_locked(self):
        """Return true if the pid lock exists."""
        return os.path.exists(self.path)

    def release(self, *args):
        """Release lock."""
        self.remove()
    __exit__ = release

    def read_pid(self):
        """Read and return the current pid."""
        with ignore_errno('ENOENT'):
            with open(self.path, 'r') as fh:
                line = fh.readline()
                if line.strip() == line:  # must contain '\n'
                    raise ValueError(
                        'Partial or invalid pidfile {0.path}'.format(self))

                try:
                    return int(line.strip())
                except ValueError:
                    raise ValueError(
                        'pidfile {0.path} contents invalid.'.format(self))

    def remove(self):
        """Remove the lock."""
        with ignore_errno(errno.ENOENT, errno.EACCES):
            os.unlink(self.path)

    def remove_if_stale(self):
        """Remove the lock if the process is not running.
        (does not respond to signals)."""
        try:
            pid = self.read_pid()
        except ValueError as exc:
            print('Broken pidfile found. Removing it.', file=sys.stderr)
            self.remove()
            return True
        if not pid:
            self.remove()
            return True

        try:
            os.kill(pid, 0)
        except os.error as exc:
            if exc.errno == errno.ESRCH:
                print('Stale pidfile exists. Removing it.', file=sys.stderr)
                self.remove()
                return True
        return False

    def write_pid(self):
        pid = os.getpid()
        content = '{0}\n'.format(pid)

        pidfile_fd = os.open(self.path, PIDFILE_FLAGS, PIDFILE_MODE)
        pidfile = os.fdopen(pidfile_fd, 'w')
        try:
            pidfile.write(content)
            # flush and sync so that the re-read below works.
            pidfile.flush()
            try:
                os.fsync(pidfile_fd)
            except AttributeError:  # pragma: no cover
                pass
        finally:
            pidfile.close()

        rfh = open(self.path)
        try:
            if rfh.read() != content:
                raise LockFailed(
                    "Inconsistency: Pidfile content doesn't match at re-read")
        finally:
            rfh.close()
PIDFile = Pidfile  # compat alias


def create_pidlock(pidfile):
    """Create and verify pidfile.

    If the pidfile already exists the program exits with an error message,
    however if the process it refers to is not running anymore, the pidfile
    is deleted and the program continues.

    This function will automatically install an :mod:`atexit` handler
    to release the lock at exit, you can skip this by calling
    :func:`_create_pidlock` instead.

    :returns: :class:`Pidfile`.

    **Example**:

    .. code-block:: python

        pidlock = create_pidlock('/var/run/app.pid')

    """
    pidlock = _create_pidlock(pidfile)
    atexit.register(pidlock.release)
    return pidlock


def _create_pidlock(pidfile):
    pidlock = Pidfile(pidfile)
    if pidlock.is_locked() and not pidlock.remove_if_stale():
        print(PIDLOCKED.format(pidfile, pidlock.read_pid()), file=sys.stderr)
        raise SystemExit(EX_CANTCREAT)
    pidlock.acquire()
    return pidlock


