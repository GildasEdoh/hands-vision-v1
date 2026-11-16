import time
from threading import Lock
from typing import Callable


class MonotonicMillisecondClock:
    def __init__(self, clock_ns: Callable[[], int] = time.monotonic_ns):
        self._clock_ns = clock_ns
        self._last_timestamp_ms = -1
        self._lock = Lock()

    def next(self) -> int:
        with self._lock:
            current_timestamp_ms = self._clock_ns() // 1_000_000
            self._last_timestamp_ms = max(
                current_timestamp_ms,
                self._last_timestamp_ms + 1,
            )
            return self._last_timestamp_ms
