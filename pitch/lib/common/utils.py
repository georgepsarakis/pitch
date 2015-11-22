from __future__ import unicode_literals
from functools import wraps
import operator
import inspect
import re
import sys
import logging
from logging import StreamHandler
from pprint import PrettyPrinter
import six

# Regular Expressions
RE_FIND_SCHEME = re.compile(r'http[s]*://')
# Logging/Debugging
debug = PrettyPrinter(indent=4).pformat
error_logger = logging.getLogger('pitch.errors')
info_logger = logging.getLogger('pitch.feedback')


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


def type_guard(**kwargs):
    specification = kwargs

    def outer_wrapper(f):
        @wraps(f)
        def inner_wrapper(*args, **inner_kwargs):
            signature = inspect.getargspec(f)
            kw_arguments = {}
            if args:
                kw_arguments = {
                    signature.args[index]: value
                    for index, value in enumerate(args)
                }
            kw_arguments.update(inner_kwargs)
            for argument, arg_type in six.iteritems(specification):
                if argument in kw_arguments:
                    if not isinstance(inner_kwargs[argument], arg_type):
                        raise TypeError(
                            '{}->{}: Argument {} requires {}'.format(
                                f.__module__,
                                f.__name__,
                                argument,
                                map(
                                    operator.attrgetter('__name__'),
                                    to_iterable(arg_type)
                                )
                            )
                        )
            return f(*args, **inner_kwargs)
        return inner_wrapper
    return outer_wrapper


def get_exported_plugins(base_class):
    return {
        cls.get_name(): cls
        for cls in base_class.__subclasses__()
    }