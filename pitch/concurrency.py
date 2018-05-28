from abc import abstractmethod

from concurrent import futures


class Pool(object):
    def __init__(self, loops=1, concurrency=1):
        self._concurrency = concurrency
        self._loops = loops

    @abstractmethod
    @property
    def executor_class(self) -> futures.Executor:
        pass

    def run(self, fn, *args, **kwargs):
        promises = []

        with self.executor_class(max_workers=self._concurrency) as pool:
            for loop in range(self._loops):
                promises.append(
                    pool.submit(fn, *args, **kwargs)
                )

        return promises, [p.exception() for p in promises]


class ThreadPool(Pool):
    @property
    def executor_class(self):
        return futures.ThreadPoolExecutor


class ProcessPool(Pool):
    @property
    def executor_class(self):
        return futures.ProcessPoolExecutor


class AsyncIOPool(Pool):
    pass
