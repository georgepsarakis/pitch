from setuptools import setup, find_packages

from pitch.version import get_version

setup(
    name='pitch',
    version=get_version(),
    author='George Psarakis',
    author_email='giwrgos.psarakis@gmail.com',
    install_requires=[
        'PyYaml==3.12',
        'boltons==18.0.0',
        'click==6.7',
        'colorama==0.3.9',
        'jinja2==2.10',
        'marshmallow==2.15.3',
        'requests==2.18.4',
        'structlog==18.1.0'
    ],
    tests_require=[
        'responses==0.9.0'
    ],
    packages=list(
        filter(lambda pkg: pkg.startswith('pitch'), find_packages())
    ),
    pythons_requires='>=3.6.0',
    entry_points={
        'console_scripts': [
            'pitch=pitch.cli.main:cli',
        ]
    }
)
