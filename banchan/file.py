import os


def verify_directory(dir):
    """verifies and creates a directory.  tries to
    ignore collisions with other threads and processes."""

    tries = 0
    while not os.access(dir, os.F_OK):
        try:
            tries += 1
            os.makedirs(dir)
        except:
            if tries > 5:
                raise


def check_is_writeable(path):
    try:
        f = open(path, 'a')
    except IOError as e:
        raise RuntimeError("Error: '%s' isn't writable [%r]" % (path, e))
    f.close()


def is_fileobject(obj):
    if not hasattr(obj, "tell") or not hasattr(obj, "fileno"):
        return False

    # check BytesIO case and maybe others
    try:
        obj.fileno()
    except (IOError, io.UnsupportedOperation):
        return False

    return True


class Tee(object):
    """A class to duplicate an output stream to stdout/err.

    This works in a manner very similar to the Unix 'tee' command.

    When the object is closed or deleted, it closes the original file given to
    it for duplication.
    """
    # Inspired by:
    # http://mail.python.org/pipermail/python-list/2007-May/442737.html

    def __init__(self, file_or_name, mode="w", channel='stdout'):
        """Construct a new Tee object.

        Parameters
        ----------
        file_or_name : filename or open filehandle (writable)
          File that will be duplicated

        mode : optional, valid mode for open().
          If a filename was give, open with this mode.

        channel : str, one of ['stdout', 'stderr']
        """
        if channel not in ['stdout', 'stderr']:
            raise ValueError('Invalid channel spec %s' % channel)

        if hasattr(file_or_name, 'write') and hasattr(file_or_name, 'seek'):
            self.file = file_or_name
        else:
            self.file = open(file_or_name, mode)
        self.channel = channel
        self.ostream = getattr(sys, channel)
        setattr(sys, channel, self)
        self._closed = False

    def close(self):
        """Close the file and restore the channel."""
        self.flush()
        setattr(sys, self.channel, self.ostream)
        self.file.close()
        self._closed = True

    def write(self, data):
        """Write data to both channels."""
        self.file.write(data)
        self.ostream.write(data)
        self.ostream.flush()

    def flush(self):
        """Flush both channels."""
        self.file.flush()
        self.ostream.flush()

    def __del__(self):
        if not self._closed:
            self.close()


def get_home_dir(require_writable=False):
    """Return the 'home' directory, as a unicode string.

    Uses os.path.expanduser('~'), and checks for writability.

    See stdlib docs for how this is determined.
    $HOME is first priority on *ALL* platforms.

    Parameters
    ----------

    require_writable : bool [default: False]
        if True:
            guarantees the return value is a writable directory, otherwise
            raises HomeDirError
        if False:
            The path is resolved, but it is not guaranteed to exist or be writable.
    """

    homedir = os.path.expanduser('~')
    # Next line will make things work even when /home/ is a symlink to
    # /usr/home as it is on FreeBSD, for example
    homedir = os.path.realpath(homedir)

    if not _writable_dir(homedir) and os.name == 'nt':
        # expanduser failed, use the registry to get the 'My Documents' folder.
        try:
            try:
                import winreg as wreg  # Py 3
            except ImportError:
                import _winreg as wreg  # Py 2
            key = wreg.OpenKey(
                wreg.HKEY_CURRENT_USER,
                "Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            homedir = wreg.QueryValueEx(key,'Personal')[0]
            key.Close()
        except:
            pass

    if (not require_writable) or _writable_dir(homedir):
        return py3compat.cast_unicode(homedir, fs_encoding)
    else:
        raise HomeDirError('%s is not a writable dir, '
                'set $HOME environment variable to override' % homedir)


def open_if_exists(filename, mode='rb'):
    """Returns a file descriptor for the filename if that file exists,
    otherwise `None`.
    """
    try:
        return open(filename, mode)
    except IOError as e:
        if e.errno not in (errno.ENOENT, errno.EISDIR, errno.EINVAL):
            raise

def ls_tree(dir_path="",
            skip_pattern=skip_pattern,
            indent="|-- ", branch_indent="|   ",
            last_indent="`-- ", last_branch_indent="    "):
    # TODO: empty directories look like non-directory files
    return "\n".join(_ls_tree_lines(dir_path, skip_pattern,
                                    indent, branch_indent,
                                    last_indent, last_branch_indent))


def _ls_tree_lines(dir_path, skip_pattern,
                   indent, branch_indent, last_indent, last_branch_indent):
    if dir_path == "":
        dir_path = os.getcwd()

    lines = []

    names = os.listdir(dir_path)
    names.sort()
    dirs, nondirs = [], []
    for name in names:
        if re.match(skip_pattern, name):
            continue
        if os.path.isdir(os.path.join(dir_path, name)):
            dirs.append(name)
        else:
            nondirs.append(name)

    # list non-directories first
    entries = list(itertools.chain([(name, False) for name in nondirs],
                                   [(name, True) for name in dirs]))
    def ls_entry(name, is_dir, ind, branch_ind):
        if not is_dir:
            yield ind + name
        else:
            path = os.path.join(dir_path, name)
            if not os.path.islink(path):
                yield ind + name
                subtree = _ls_tree_lines(path, skip_pattern,
                                         indent, branch_indent,
                                         last_indent, last_branch_indent)
                for x in subtree:
                    yield branch_ind + x
    for name, is_dir in entries[:-1]:
        for line in ls_entry(name, is_dir, indent, branch_indent):
            yield line
    if entries:
        name, is_dir = entries[-1]
        for line in ls_entry(name, is_dir, last_indent, last_branch_indent):
            yield line


def absdir(path):
    """Return absolute, normalized path to directory, if it exists; None
    otherwise.
    """
    if not os.path.isabs(path):
        path = os.path.normpath(os.path.abspath(os.path.join(os.getcwd(),
                                                             path)))
    if path is None or not os.path.isdir(path):
        return None
    return path


def absfile(path, where=None):
    """Return absolute, normalized path to file (optionally in directory
    where), or None if the file can't be found either in where or the current
    working directory.
    """
    orig = path
    if where is None:
        where = os.getcwd()
    if isinstance(where, list) or isinstance(where, tuple):
        for maybe_path in where:
            maybe_abs = absfile(path, maybe_path)
            if maybe_abs is not None:
                return maybe_abs
        return None
    if not os.path.isabs(path):
        path = os.path.normpath(os.path.abspath(os.path.join(where, path)))
    if path is None or not os.path.exists(path):
        if where != os.getcwd():
            # try the cwd instead
            path = os.path.normpath(os.path.abspath(os.path.join(os.getcwd(),
                                                                 orig)))
    if path is None or not os.path.exists(path):
        return None
    if os.path.isdir(path):
        # might want an __init__.py from pacakge
        init = os.path.join(path,'__init__.py')
        if os.path.isfile(init):
            return init
    elif os.path.isfile(path):
        return path
    return None


def file_like(name):
    """A name is file-like if it is a path that exists, or it has a
    directory part, or it ends in .py, or it isn't a legal python
    identifier.
    """
    return (os.path.exists(name)
            or os.path.dirname(name)
            or name.endswith('.py')
            or not ident_re.match(os.path.splitext(name)[0]))


def func_lineno(func):
    """Get the line number of a function. First looks for
    compat_co_firstlineno, then func_code.co_first_lineno.
    """
    try:
        return func.compat_co_firstlineno
    except AttributeError:
        try:
            return func.func_code.co_firstlineno
        except AttributeError:
            return -1


def is_executable(file):
    if not os.path.exists(file):
        return False
    st = os.stat(file)
    return bool(st.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH))


def ensure_dir(path):
    """os.path.makedirs without EEXIST."""
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


def file_contents(filename):
    with open(filename, 'rb') as fp:
        return fp.read().decode('utf-8')


def read_chunks(file, size=4096):
    """Yield pieces of data from a file-like object until EOF."""
    while True:
        chunk = file.read(size)
        if not chunk:
            break
        yield chunk


def split_leading_dir(path):
    path = path.lstrip('/').lstrip('\\')
    if '/' in path and (('\\' in path and path.find('/') < path.find('\\')) or
                        '\\' not in path):
        return path.split('/', 1)
    elif '\\' in path:
        return path.split('\\', 1)
    else:
        return path, ''


def has_leading_dir(paths):
    """Returns true if all the paths have the same leading path name
    (i.e., everything is in one subdirectory in an archive)"""
    common_prefix = None
    for path in paths:
        prefix, rest = split_leading_dir(path)
        if not prefix:
            return False
        elif common_prefix is None:
            common_prefix = prefix
        elif prefix != common_prefix:
            return False
    return True


def normalize_path(path, resolve_symlinks=True):
    """
    Convert a path to its canonical, case-normalized, absolute version.

    """
    path = expanduser(path)
    if resolve_symlinks:
        path = os.path.realpath(path)
    else:
        path = os.path.abspath(path)
    return os.path.normcase(path)


def read_text_file(filename):
    """Return the contents of *filename*.

    Try to decode the file contents with utf-8, the preferred system encoding
    (e.g., cp1252 on some Windows machines), and latin1, in that order.
    Decoding a byte string with latin1 will never raise an error. In the worst
    case, the returned string will contain some garbage characters.

    """
    with open(filename, 'rb') as fp:
        data = fp.read()

    encodings = ['utf-8', locale.getpreferredencoding(False), 'latin1']
    for enc in encodings:
        try:
            data = data.decode(enc)
        except UnicodeDecodeError:
            continue
        break

    assert type(data) != bytes  # Latin1 should have worked.
    return data


def ensuredir(path):
    """Ensure that a path exists."""
    try:
        os.makedirs(path)
    except OSError as err:
        # 0 for Jython/Win32
        if err.errno not in [0, EEXIST]:
            raise


# This function is same as os.walk of Python2.6, 2.7, 3.2, 3.3 except a
# customization that check UnicodeError.
# The customization obstacle to replace the function with the os.walk.
def walk(top, topdown=True, followlinks=False):
    """Backport of os.walk from 2.6, where the *followlinks* argument was
    added.
    """
    names = os.listdir(top)

    dirs, nondirs = [], []
    for name in names:
        try:
            fullpath = path.join(top, name)
        except UnicodeError:
            print('%s:: ERROR: non-ASCII filename not supported on this '
                  'filesystem encoding %r, skipped.' % (name, fs_encoding),
                  file=sys.stderr)
            continue
        if path.isdir(fullpath):
            dirs.append(name)
        else:
            nondirs.append(name)

    if topdown:
        yield top, dirs, nondirs
    for name in dirs:
        fullpath = path.join(top, name)
        if followlinks or not path.islink(fullpath):
            for x in walk(fullpath, topdown, followlinks):
                yield x
    if not topdown:
        yield top, dirs, nondirs


def mtimes_of_files(dirnames, suffix):
    for dirname in dirnames:
        for root, dirs, files in os.walk(dirname):
            for sfile in files:
                if sfile.endswith(suffix):
                    try:
                        yield path.getmtime(path.join(root, sfile))
                    except EnvironmentError:
                        pass


def movefile(source, dest):
    """Move a file, removing the destination if it exists."""
    if os.path.exists(dest):
        try:
            os.unlink(dest)
        except OSError:
            pass
    os.rename(source, dest)


def copytimes(source, dest):
    """Copy a file's modification times."""
    st = os.stat(source)
    if hasattr(os, 'utime'):
        os.utime(dest, (st.st_atime, st.st_mtime))


def copyfile(source, dest):
    """Copy a file and its modification times, if possible."""
    shutil.copyfile(source, dest)
    try:
        # don't do full copystat because the source may be read-only
        copytimes(source, dest)
    except OSError:
        pass


no_fn_re = re.compile(r'[^a-zA-Z0-9_-]')


def make_filename(string):
    return no_fn_re.sub('', string) or 'sphinx'


def ustrftime(format, *args):
    # strftime for unicode strings
    if not args:
        # If time is not specified, try to use $SOURCE_DATE_EPOCH variable
        # See https://wiki.debian.org/ReproducibleBuilds/TimestampsProposal
        source_date_epoch = os.getenv('SOURCE_DATE_EPOCH')
        if source_date_epoch is not None:
            time_struct = time.gmtime(float(source_date_epoch))
            args = [time_struct]
    if PY2:
        # if a locale is set, the time strings are encoded in the encoding
        # given by LC_TIME; if that is available, use it
        enc = locale.getlocale(locale.LC_TIME)[1] or 'utf-8'
        return time.strftime(text_type(format).encode(enc), *args).decode(enc)
    else:  # Py3
        # On Windows, time.strftime() and Unicode characters will raise UnicodeEncodeError.
        # http://bugs.python.org/issue8304
        try:
            return time.strftime(format, *args)
        except UnicodeEncodeError:
            r = time.strftime(format.encode('unicode-escape').decode(), *args)
            return r.encode().decode('unicode-escape')


def safe_relpath(path, start=None):
    try:
        return os.path.relpath(path, start)
    except ValueError:
        return path


fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()


def abspath(pathdir):
    pathdir = path.abspath(pathdir)
    if isinstance(pathdir, bytes):
        pathdir = pathdir.decode(fs_encoding)
    return pathdir


def getcwd():
    if hasattr(os, 'getcwdu'):
        return os.getcwdu()
    return os.getcwd()


@contextlib.contextmanager
def cd(target_dir):
    cwd = getcwd()
    try:
        os.chdir(target_dir)
        yield
    finally:
        os.chdir(cwd)


def unfrackpath(path):
    '''
    returns a path that is free of symlinks, environment
    variables, relative path traversals and symbols (~)
    example:
    '$HOME/../../var/mail' becomes '/var/spool/mail'
    '''
    return os.path.normpath(os.path.realpath(os.path.expandvars(os.path.expanduser(path))))


def makedirs_safe(path, mode=None):
    '''Safe way to create dirs in muliprocess/thread environments'''
    if not os.path.exists(path):
        try:
            if mode:
                os.makedirs(path, mode)
            else:
                os.makedirs(path)
        except OSError as e:
            if e.errno != EEXIST:
                raise


def is_executable(path):
    '''is the given path executable?'''
    return (stat.S_IXUSR & os.stat(path)[stat.ST_MODE]
            or stat.S_IXGRP & os.stat(path)[stat.ST_MODE]
            or stat.S_IXOTH & os.stat(path)[stat.ST_MODE])
