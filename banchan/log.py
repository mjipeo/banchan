import cPickle as pickle
import logging
import SocketServer
import select
import socket
import struct
import sys
import warnings
from logging.config import dictConfig

from .text import convert_to_byte, truncate as truncate_string


try:
    import curses
    curses.setupterm()
except:
    curses = None


# Formatters
# ----------


class ColorFormatter(logging.Formatter):
    def __init__(self, color=True, *args, **kwargs):
        super(ColorFormatter, self).__init__(*args, **kwargs)

        self._color = color
        self._color_map = None

    @property
    def color_map(self):
        if self._color_map is None:
            fg_color = (curses.tigetstr('setaf') or
                        curses.tigetstr('setf') or '')
            self._color_map = {
                logging.INFO: unicode(curses.tparm(fg_color, 2),     # Green
                                      'ascii'),
                logging.WARNING: unicode(curses.tparm(fg_color, 3),  # Yellow
                                         'ascii'),
                logging.ERROR: unicode(curses.tparm(fg_color, 1),    # Red
                                       'ascii'),
                logging.CRITICAL: unicode(curses.tparm(fg_color, 1), # Red
                                          'ascii'),
            }
            self._normal_color = unicode(curses.tigetstr('sgr0'), 'ascii')
        return self._color_map

    def format(self, record):
        formatted = super(ColorFormatter, self).format(record)
        if self._color:
            prefix = self.color_map.get(record.levelno, self._normal_color)
            formatted = \
                convert_to_byte(prefix) \
                + convert_to_byte(formatted) \
                + convert_to_byte(self._normal_color)
        return formatted


# Filters
# -------

class AddHostInfoFilter(logging.Filter):
    def filter(self, record):
        record.host = socket.gethostname()
        return True


# Collector
# ---------

class RemoteLogHandler(logging.handlers.SocketHandler):
    default_collector_host = '127.0.0.1'
    default_collector_port = 8543

    def __init__(self, host=default_collector_host,
                 port=default_collector_port):
        logging.handlers.SocketHandler.__init__(self, host, port)


class RemoteLogStreamHandler(SocketServer.StreamRequestHandler):
    def _unpickle(self, data):
        return pickle.loads(data)

    def handle(self):
        """
        Handle multiple requests - each expected to be a 4-byte length,
        followed by the LogRecord in pickle format. Logs the record
        according to whatever policy is configured locally.
        """
        while True:
            chunk = self.connection.recv(4)
            if len(chunk) < 4:
                break
            slen = struct.unpack('>L', chunk)[0]
            chunk = self.connection.recv(slen)
            while len(chunk) < slen:
                chunk = chunk + self.connection.recv(slen - len(chunk))
            obj = self._unpickle(chunk)
            record = logging.makeLogRecord(obj)
            self.handle_log_record(record)

    def handle_log_record(self, record):
        logging.getLogger('collector').handle(record)


class RemoteLogCollector(SocketServer.ThreadingTCPServer):
    allow_reuse_address = 1
    default_collector_bind = '127.0.0.1'
    default_collector_port = RemoteLogHandler.default_collector_port

    def __init__(self, host=default_collector_bind,
                 port=default_collector_port, handler=RemoteLogStreamHandler):
        SocketServer.ThreadingTCPServer.__init__(self, (host, port), handler)
        self.abort = 0
        self.timeout = 1

    def serve_until_stopped(self):
        abort = 0
        while not abort:
            rd, wr, ex = select.select([self.socket.fileno()],
                                       [], [],
                                       self.timeout)
            if rd:
                self.handle_request()
            abort = self.abort

    def start(self):
        self.serve_until_stopped()


# Utils
# -----

class LogMixin(object):
    logger_name = None
    log_format = u'{label:34} {msg}'

    def __init__(self, *args, **kwargs):
        super(LogMixin, self).__init__(*args, **kwargs)
        self._logger = None
        self._logger_label = None

    def __unicode__(self):
        return self.__class__.__name__

    __repr__ = __unicode__

    @property
    def logger_label(self):
        if not self._logger_label:
            self._logger_label = self.__unicode__()
        return self._logger_label

    @property
    def logger(self):
        if self._logger is None:
            self._logger = logging.getLogger(
                self.logger_name or self.__class__.__module__)
        return self._logger

    def set_logger_label(self, label):
        self._logger_label = label

    def get_log_msg(self, msg, truncate=False):
        formatted = self.log_format.format(label=self.logger_label, msg=msg)
        return truncate_string(formatted) if truncate else formatted

    def debug(self, msg, *args, **kwargs):
        truncate = kwargs.pop('truncate', False)
        self.logger.debug(self.get_log_msg(msg, truncate), *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        truncate = kwargs.pop('truncate', False)
        self.logger.info(self.get_log_msg(msg, truncate), *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        truncate = kwargs.pop('truncate', False)
        self.logger.warn(self.get_log_msg(msg, truncate), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        truncate = kwargs.pop('truncate', False)
        self.logger.error(self.get_log_msg(msg, truncate), *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        truncate = kwargs.pop('truncate', False)
        self.logger.critical(self.get_log_msg(msg, truncate), *args, **kwargs)


def configure_logging(logging_settings):
    if not sys.warnoptions:
        # Route warnings through python logging
        logging.captureWarnings(True)
        # Allow DeprecationWarnings through the warnings filters
        warnings.simplefilter('default', DeprecationWarning)

    logging_config_func = dictConfig
    logging_config_func(logging_settings)


##


import logging
import sys

# set initial level to WARN.  This so that
# log statements don't occur in the absence of explicit
# logging being enabled for 'sqlalchemy'.
rootlogger = logging.getLogger('sqlalchemy')
if rootlogger.level == logging.NOTSET:
    rootlogger.setLevel(logging.WARN)


def _add_default_handler(logger):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(message)s'))
    logger.addHandler(handler)


_logged_classes = set()


def class_logger(cls):
    logger = logging.getLogger(cls.__module__ + "." + cls.__name__)
    cls._should_log_debug = lambda self: logger.isEnabledFor(logging.DEBUG)
    cls._should_log_info = lambda self: logger.isEnabledFor(logging.INFO)
    cls.logger = logger
    _logged_classes.add(cls)
    return cls


class Identified(object):
    logging_name = None

    def _should_log_debug(self):
        return self.logger.isEnabledFor(logging.DEBUG)

    def _should_log_info(self):
        return self.logger.isEnabledFor(logging.INFO)


class InstanceLogger(object):
    """A logger adapter (wrapper) for :class:`.Identified` subclasses.

    This allows multiple instances (e.g. Engine or Pool instances)
    to share a logger, but have its verbosity controlled on a
    per-instance basis.

    The basic functionality is to return a logging level
    which is based on an instance's echo setting.

    Default implementation is:

    'debug' -> logging.DEBUG
    True    -> logging.INFO
    False   -> Effective level of underlying logger
               (logging.WARNING by default)
    None    -> same as False
    """

    # Map echo settings to logger levels
    _echo_map = {
        None: logging.NOTSET,
        False: logging.NOTSET,
        True: logging.INFO,
        'debug': logging.DEBUG,
    }

    def __init__(self, echo, name):
        self.echo = echo
        self.logger = logging.getLogger(name)

        # if echo flag is enabled and no handlers,
        # add a handler to the list
        if self._echo_map[echo] <= logging.INFO \
           and not self.logger.handlers:
            _add_default_handler(self.logger)

    #
    # Boilerplate convenience methods
    #
    def debug(self, msg, *args, **kwargs):
        """Delegate a debug call to the underlying logger."""

        self.log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Delegate an info call to the underlying logger."""

        self.log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Delegate a warning call to the underlying logger."""

        self.log(logging.WARNING, msg, *args, **kwargs)

    warn = warning

    def error(self, msg, *args, **kwargs):
        """
        Delegate an error call to the underlying logger.
        """
        self.log(logging.ERROR, msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """Delegate an exception call to the underlying logger."""

        kwargs["exc_info"] = 1
        self.log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Delegate a critical call to the underlying logger."""

        self.log(logging.CRITICAL, msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        """Delegate a log call to the underlying logger.

        The level here is determined by the echo
        flag as well as that of the underlying logger, and
        logger._log() is called directly.

        """

        # inline the logic from isEnabledFor(),
        # getEffectiveLevel(), to avoid overhead.

        if self.logger.manager.disable >= level:
            return

        selected_level = self._echo_map[self.echo]
        if selected_level == logging.NOTSET:
            selected_level = self.logger.getEffectiveLevel()

        if level >= selected_level:
            self.logger._log(level, msg, args, **kwargs)

    def isEnabledFor(self, level):
        """Is this logger enabled for level 'level'?"""

        if self.logger.manager.disable >= level:
            return False
        return level >= self.getEffectiveLevel()

    def getEffectiveLevel(self):
        """What's the effective level for this logger?"""

        level = self._echo_map[self.echo]
        if level == logging.NOTSET:
            level = self.logger.getEffectiveLevel()
        return level


def instance_logger(instance, echoflag=None):
    """create a logger for an instance that implements :class:`.Identified`."""

    if instance.logging_name:
        name = "%s.%s.%s" % (instance.__class__.__module__,
                             instance.__class__.__name__,
                             instance.logging_name)
    else:
        name = "%s.%s" % (instance.__class__.__module__,
                          instance.__class__.__name__)

    instance._echo = echoflag

    if echoflag in (False, None):
        # if no echo setting or False, return a Logger directly,
        # avoiding overhead of filtering
        logger = logging.getLogger(name)
    else:
        # if a specified echo flag, return an EchoLogger,
        # which checks the flag, overrides normal log
        # levels by calling logger._log()
        logger = InstanceLogger(echoflag, name)

    instance.logger = logger


class echo_property(object):
    __doc__ = """\
    When ``True``, enable log output for this element.

    This has the effect of setting the Python logging level for the namespace
    of this element's class and object reference.  A value of boolean ``True``
    indicates that the loglevel ``logging.INFO`` will be set for the logger,
    whereas the string value ``debug`` will set the loglevel to
    ``logging.DEBUG``.
    """

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            return instance._echo

    def __set__(self, instance, value):
        instance_logger(instance, echoflag=value)
