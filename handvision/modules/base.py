from abc import ABC, abstractmethod
from typing import Sequence

import numpy as np

from handvision.interfaces import Landmark


class VisionModule(ABC):
    """Feature interface used by the shared capture and hand-detection pipeline.

    Frame processing and normal resource cleanup run on the processing worker.
    """

    @abstractmethod
    def process_frame(
        self,
        frame: np.ndarray,
        landmarks: Sequence[Landmark],
        *,
        fps: float,
        elapsed_seconds: float,
    ) -> np.ndarray:
        """Apply one feature module to a frame from the shared vision pipeline."""

    def close(self) -> None:
        """Release resources owned by the module."""
