from __future__ import unicode_literals
import six
from ..lib.scheme.structures import SchemeExecutor
from ..lib.common.structures import InstanceInfo


class PitchRunner(object):
    def __init__(self, scheme_loader):
        self._scheme_loader = scheme_loader
        self._responses = []

    @property
    def scheme_loader(self):
        return self._scheme_loader

    def run(self, process_id):
        scheme = self._scheme_loader.scheme
        threads = scheme.get('threads', 1)
        loops = scheme.get('repeat', 1)
        results = []
        future_schemes = []
        if threads == 1:
            instance = InstanceInfo(
                process_id=1,
                loop_id=0,
                threads=1
            )
            executor = SchemeExecutor(self._scheme_loader, instance)
            executor.execute_scheme()
        else:
            from concurrent import futures
            with futures.ThreadPoolExecutor(max_workers=threads) as pool:
                for loop_id in range(loops):
                    instance = InstanceInfo(
                        process_id=process_id,
                        loop_id=loop_id,
                        threads=threads
                    )
                    executor = SchemeExecutor(self._scheme_loader, instance)
                    future_schemes.append(
                        pool.submit(executor.execute_scheme)
                    )
                futures.wait(future_schemes)
                exceptions = [f.exception() for f in future_schemes]
                for exception in exceptions:
                    six.print_('Exception:{}'.format(exception))
        return results
