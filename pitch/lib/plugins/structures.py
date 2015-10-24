from __future__ import unicode_literals
from copy import copy
from collections import MutableSequence


class PitchPluginCollection(MutableSequence):
    def __init__(self, plugin_list=None):
        if plugin_list is None:
            self._plugins = []
        else:
            self._plugins = copy(plugin_list)

    def __getitem__(self, index):
        return self._plugins[index]

    def __setitem__(self, index, value):
        self._plugins[index] = value

    def __delitem__(self, index):
        del self._plugins[index]

    def __len__(self):
        return self._plugins.__len__()

    def get(self, name):
        return_plugin = None
        for plugin in self._plugins:
            if name == plugin['plugin']:
                return_plugin = plugin
        return return_plugin

    def get_list(self, name):
        return_plugins = None
        for plugin in self._plugins:
            if name == plugin['plugin']:
                if return_plugins is None:
                    return_plugins = []
                return_plugins.append(plugin)
        return return_plugins

    def insert(self, index, value):
        self._plugins.insert(index, value)
