#!/usr/bin/env python
import subprocess
import sys

if __name__ == "__main__":
    api_names = [
        'github',
        'stack-exchange'
    ]
    for api_name in api_names:
        try:
            subprocess.call(
                [
                    'pitch',
                    '-S',
                    'json_api_schemes/{}-scheme.yml'.format(api_name)
                ]
            )
        except subprocess.CalledProcessError as e:
            print '-- API TEST ERROR: {}'.format(api_name)
            print e
            sys.exit(e.returncode)
