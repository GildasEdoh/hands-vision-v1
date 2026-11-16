from queue import Empty, Full, Queue
from threading import Lock
from typing import Generic, TypeVar


T = TypeVar("T")


class LatestFrameQueue(Generic[T]):
    """A one-item queue that replaces stale frames with the newest frame."""

    def __init__(self):
        self._queue = Queue(maxsize=1)
        self._put_lock = Lock()
        self.replaced_count = 0

    def put_latest(self, item: T) -> None:
        with self._put_lock:
            try:
                self._queue.put_nowait(item)
            except Full:
                self.replaced_count += 1
                try:
                    self._queue.get_nowait()
                except Empty:
                    pass
                self._queue.put_nowait(item)

    def get(self, timeout=None) -> T:
        return self._queue.get(timeout=timeout)

    def get_nowait(self) -> T:
        return self._queue.get_nowait()
