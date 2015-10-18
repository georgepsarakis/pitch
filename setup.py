from setuptools import setup, find_packages
from pitch.version import get_version

setup(
    name='pitch',
    version=get_version(),
    author='George Psarakis',
    author_email='giwrgos.psarakis@gmail.com',
    install_requires=[
        'requests',       # URL fetching
        'argparse',       # Argument parsing (command-line use only)
        'futures',        # Multi-threading
        'PyYaml',         # Configuration files
        'jinja2',         # Template engine
        'six'             # Python 2/3 compatibility
    ],
    packages=list(
        filter(lambda pkg: pkg.startswith('pitch'), find_packages())
    ),
    entry_points={
        'console_scripts': [
            'pitch=pitch.main:main',
        ]
    }
)
