from __future__ import unicode_literals
from ..lib.scheme.structures import SchemeLoader
from ..lib.plugins.utils import loader as plugin_loader, list_plugins
from .structures import PitchRunner


def start_process(scheme, process_id=1):
    scheme_loader = SchemeLoader(scheme)
    runner = PitchRunner(scheme_loader)
    runner.run(process_id)


def bootstrap(**kwargs):
    scheme = kwargs['scheme']
    processes = kwargs.get('processes', 1)
    plugin_loader(
        kwargs.get('request_plugins_modules'),
        kwargs.get('response_plugins_modules')
    )
    if kwargs.get('list_plugins'):
        list_plugins()
    if processes > 1:
        from concurrent import futures
        with futures.ProcessPoolExecutor(max_workers=processes) as pool:
            future_list = []
            for pid in range(1, processes + 1):
                future_list.append(
                    pool.submit(start_process, scheme, pid)
                )
            futures.wait(future_list)
    else:
        start_process(scheme)
