from pitch.sequence.executor import SequenceLoader
from pitch.plugins.utils import loader as plugin_loader
from pitch.runner.structures import PitchRunner


def start_process(sequence, logger):
    sequence_loader = SequenceLoader(sequence)
    runner = PitchRunner(sequence_loader, logger=logger)
    runner.run()


def bootstrap(**kwargs):
    scheme = kwargs['sequence_file']
    logger = kwargs['logger']
    plugin_loader(
        kwargs.get('request_plugins'),
        kwargs.get('response_plugins')
    )

    start_process(scheme, logger=logger)
