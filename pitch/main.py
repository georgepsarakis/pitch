#!/usr/bin/env python
from __future__ import unicode_literals
import argparse
import os
import sys


PATH = os.path.dirname(os.path.abspath(__file__))


def main():
    try:
        import pitch # flake8: noqa
    except ImportError:
        sys.path.append(
            os.path.abspath(os.path.join(PATH, '../'))
        )
    from pitch.runner.bootstrap import bootstrap
    from pitch.version import get_version

    arg_parser = argparse.ArgumentParser(
        'pitch v{}'.format(get_version())
    )
    arg_parser.add_argument(
        '--version',
        action='version',
        version=get_version()
    )
    arg_parser.add_argument(
        '-P',
        '--processes',
        help='Number of processes',
        type=int,
        default=1
    )
    arg_parser.add_argument(
        '--request-plugins-modules',
        nargs='*',
        help='Additional request plugins (in Python import notation)'
    )
    arg_parser.add_argument(
        '--response-plugins-modules',
        nargs='*',
        help='Additional response plugins (in Python import notation)'
    )
    command_group = arg_parser.add_mutually_exclusive_group(required=True)
    command_group.add_argument(
        '--list-plugins',
        action='store_true',
        default=False,
        help='Display available plugins and exit.'
    )
    command_group.add_argument(
        '-S',
        '--scheme',
        help='Path of the scheme file to execute'
    )
    parameters = arg_parser.parse_args()
    bootstrap(**vars(parameters))


if __name__ == "__main__":
    main()
