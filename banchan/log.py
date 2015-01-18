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
