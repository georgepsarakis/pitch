from pitch.sequence.executor import SequenceExecutor


class PitchRunner(object):
    def __init__(self, sequence_loader, logger):
        self._sequence_loader = sequence_loader
        self._logger = logger
        self._responses = []

    @property
    def logger(self):
        return self._logger

    @property
    def sequence_loader(self):
        return self._sequence_loader

    def run(self):
        executor = SequenceExecutor(self._sequence_loader, logger=self.logger)
        return executor.run()
