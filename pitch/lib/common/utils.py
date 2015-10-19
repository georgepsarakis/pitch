from __future__ import unicode_literals
import re
import sys
import logging
from logging import StreamHandler
from pprint import PrettyPrinter

# Regular Expressions
RE_FIND_SCHEME = re.compile(r'http[s]*://')

error_logger = logging.getLogger('pitch.errors')
info_logger = logging.getLogger('pitch.feedback')

debug = PrettyPrinter(indent=4).pformat


def setup_loggers():
    def _setup_info_logger():
        info_logger.setLevel(logging.DEBUG)
        handler = StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logging.Formatter('%(message)s'))
        info_logger.addHandler(handler)

    def _setup_error_logger():
        error_logger.setLevel(logging.WARN)
        handler = StreamHandler(sys.stderr)
        handler.setLevel(logging.WARN)
        handler.setFormatter(logging.Formatter('%(message)s'))
        error_logger.addHandler(handler)

    _setup_error_logger()
    _setup_info_logger()


setup_loggers()


def stop_execution(reporter, message, exit_code=1):
    reporter(message)
    sys.exit(exit_code)


def compose_url(base_url, url):
    if RE_FIND_SCHEME.match(url) is None:
        url = '{}/{}'.format(
            base_url.rstrip('/'),
            url.lstrip('/')
        )
    return url.strip()


def identity(x):
    return x


def to_iterable(item):
    if isinstance(item, (list, tuple, set)):
        return item
    else:
        return [item]


def merge_dictionaries(a, b):
    r = a.copy()
    for k, v in b.iteritems():
        if k in r and isinstance(r[k], dict):
            r[k] = merge_dictionaries(r[k], v)
        else:
            r[k] = v
    return r


def get_exported_plugins(base_class):
    return {
        cls.get_name(): cls
        for cls in base_class.__subclasses__()
    }
