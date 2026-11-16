import math
import sys
from typing import Protocol


class VolumeController(Protocol):
    def get_volume(self) -> float: ...

    def set_volume(self, value: float) -> None: ...

    def close(self) -> None: ...


class WindowsAudioVolumeController:
    def __init__(self):
        if sys.platform != "win32":
            raise OSError("System volume control is currently supported on Windows only.")

        try:
            from pycaw.pycaw import AudioUtilities
        except ImportError as error:
            raise RuntimeError(
                "Install the project dependencies to enable Windows volume control."
            ) from error

        self._device = AudioUtilities.GetSpeakers()
        if self._device is None:
            raise RuntimeError("Windows did not provide a default playback device.")

    def get_volume(self) -> float:
        if self._device is None:
            raise RuntimeError("The Windows audio controller is closed.")
        return float(self._device.volume_percent) / 100.0

    def set_volume(self, value: float) -> None:
        if self._device is None:
            raise RuntimeError("The Windows audio controller is closed.")
        if not math.isfinite(value):
            raise ValueError("Volume must be a finite number.")
        self._device.volume_percent = max(0.0, min(100.0, value * 100.0))

    def close(self) -> None:
        self._device = None
