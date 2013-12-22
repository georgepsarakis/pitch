from setuptools import setup

setup(name='pitch',
      version='1.0',
      py_modules=['pitch'],
      author='George Psarakis',
      author_email='giwrgos.psarakis@gmail.com',
      install_requires=[
        'requests',       # URL fetching
        'argparse',       # Argument parsing (command-line use only)
        'gevent',         # Multi-threading
        'BeautifulSoup4', # Element extraction
        'PyYaml',         # Configuration files
        ],
      entry_points={
        'console_scripts': [
          'pitch = pitch:main',
        ]
      })
