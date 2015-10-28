from __future__ import unicode_literals
from datetime import datetime
import logging
import six
if six.PY2:
    from types import NoneType
else:
    NoneType = type(None)
from .utils import error_logger, info_logger, type_guard
from .structures import InstanceInfo


class ProgressLog(object):
    """ Display progress notifications using standard library logging.
    """
    LEVEL_COLOR_MAP = {
        logging.INFO: 1,
        logging.DEBUG: 34,
        logging.WARN: 33,
        logging.WARNING: 33,
        logging.ERROR: 31,
        logging.CRITICAL: 31
    }
    COLOR_CODES = {
        'red': 31,
        'blue': 34,
        'bold': 1,
        'green': 32,
        'yellow': 33
    }

    @type_guard(instance=InstanceInfo)
    def __init__(self, instance):
        self.__instance = instance

    @staticmethod
    def colorize_text(color_code, text):
        if color_code == 0:
            return text
        else:
            return "\033[{}m{}\033[0m".format(color_code, text)

    @type_guard(message=six.text_type, level=(int, NoneType), color=(int, NoneType))
    def _progress(self, message, level=None, color=None):
        if level is None:
            level = logging.INFO
        if level in [logging.WARN, logging.ERROR]:
            logger = error_logger
        else:
            logger = info_logger
        entry = "[{}] [Process={:02d},Thread={:02d},Loop={:04d}] {}".format(
            datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f'),
            self.__instance.process_id,
            self.__instance.thread_id,
            self.__instance.loop_id,
            message
        )
        if color is None:
            color = self.LEVEL_COLOR_MAP[level]
        logger.log(level, self.colorize_text(color, entry))

    def info(self, message):
        self._progress(message=message, level=logging.INFO, color=0)

    def warning(self, message):
        self._progress(message=message, level=logging.WARN)

    def error(self, message):
        self._progress(message=message, level=logging.ERROR)

    def success(self, message):
        color = self.COLOR_CODES['green']
        self._progress(message=message, level=logging.ERROR, color=color)

    def important(self, message):
        color = self.COLOR_CODES['bold']
        self._progress(message=message, level=logging.ERROR, color=color)
