from __future__ import unicode_literals
from .request import exported_plugins as request_plugins
from .response import exported_plugins as response_plugins

PLUGINS = {
    'request': request_plugins,
    'response': response_plugins
}

VALID_PHASES = PLUGINS.keys()
