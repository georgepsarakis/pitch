import logging
import time


class BasePlugin(object):
    _name = None
    _result = None

    @property
    def name(self):
        return self._name

    @property
    def phase(self):
        return self._name

    @property
    def result(self):
        return self._result

    @classmethod
    def get_name(cls):
        return cls._name

    def execute(self, plugin_context):
        pass


class LoggerPlugin(BasePlugin):
    """
    Setup a logger, attach a file handler and log a message.
    """
    _name = 'logger'

    def __init__(self, logger_name=None, message=None, **kwargs):
        if logger_name is None:
            logger_name = 'logger.plugin'
        logger_name = 'pitch.{}'.format(logger_name)
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(**kwargs.get('handler', {}))
        formatter_kwargs = kwargs.get('formatter', {})
        formatter_kwargs['fmt'] = formatter_kwargs.get(
            'fmt',
            '%(asctime)s\t%(levelname)s\t%(message)s'
        )
        formatter = logging.Formatter(**formatter_kwargs)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self._message = message

    def execute(self, plugin_context):
        self.logger.info(
            plugin_context.step['rendering'].render(self._message)
        )


class DelayPlugin(BasePlugin):
    """ Pause execution for the specified delay interval. """
    def __init__(self, seconds):
        self._delay_seconds = float(seconds)

    def execute(self, plugin_context):
        time.sleep(self._delay_seconds)


class UpdateContext(BasePlugin):
    """ Add variables to the template context. """
    def __init__(self, **updates):
        self._updates = updates

    def execute(self, plugin_context):
        plugin_context.templating['variables'].update(self._updates)
