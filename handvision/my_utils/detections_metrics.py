from collections import deque
from math import ceil
from typing import Dict, Iterable, Union


class PerformanceMetrics:
    _FIELDS = ("queue_wait_ms", "detection_ms", "drawing_ms", "processing_ms")

    def __init__(self, max_samples: int = 300):
        if max_samples < 1:
            raise ValueError("max_samples must be greater than zero.")
        self.frame_count = 0
        self._samples = deque(maxlen=max_samples)
        self._completion_times = deque(maxlen=30)
        self._display_latencies_ms = deque(maxlen=max_samples)

    def record_frame(
        self,
        queue_wait_ms: float,
        detection_ms: float,
        drawing_ms: float,
        processing_ms: float,
        completed_at: float,
    ) -> None:
        self.frame_count += 1
        self._samples.append(
            {
                "queue_wait_ms": queue_wait_ms,
                "detection_ms": detection_ms,
                "drawing_ms": drawing_ms,
                "processing_ms": processing_ms,
            }
        )
        self._completion_times.append(completed_at)

    def record_display(self, captured_at: float, displayed_at: float) -> None:
        self._display_latencies_ms.append((displayed_at - captured_at) * 1000)

    @property
    def processing_fps(self) -> float:
        if len(self._completion_times) < 2:
            return 0.0
        elapsed = self._completion_times[-1] - self._completion_times[0]
        if elapsed <= 0:
            return 0.0
        return (len(self._completion_times) - 1) / elapsed

    def summary(self) -> Dict[str, Union[float, int]]:
        result = {"frames": self.frame_count}
        if not self._samples:
            return result

        for field in self._FIELDS:
            values = [sample[field] for sample in self._samples]
            result[f"{field}_avg"] = sum(values) / len(values)
            result[f"{field}_p95"] = self._percentile_95(values)

        if self._display_latencies_ms:
            values = list(self._display_latencies_ms)
            result["display_latency_avg"] = sum(values) / len(values)
            result["display_latency_p95"] = self._percentile_95(values)
        result["processing_fps"] = self.processing_fps
        return result

    @staticmethod
    def _percentile_95(values: Iterable[float]) -> float:
        ordered = sorted(values)
        return ordered[max(0, ceil(len(ordered) * 0.95) - 1)]
