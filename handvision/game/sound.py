import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    winsound = None
    WINSOUND_AVAILABLE = False


class SoundFX:
    """Non-blocking audio feedback using winsound with safe fallback."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled and WINSOUND_AVAILABLE

    def _play_tone(self, frequency: int, duration_ms: int) -> None:
        if not self.enabled:
            return

        def _run():
            try:
                winsound.Beep(frequency, duration_ms)
            except Exception as e:
                logger.debug(f"SoundFX beep failed: {e}")

        threading.Thread(target=_run, daemon=True, name="soundfx-beep").start()

    def play_pop(self, pitch_mult: float = 1.0) -> None:
        """Crisp balloon pop sound."""
        freq = int(min(2500, max(400, 950 * pitch_mult)))
        self._play_tone(freq, 35)

    def play_golden_pop(self) -> None:
        """High-pitched reward sound for golden balloon."""
        self._play_tone(1500, 60)

    def play_miss(self) -> None:
        """Low frequency feedback when shot misses."""
        self._play_tone(350, 40)

    def play_game_over(self) -> None:
        """Descendant game over tone."""
        def _run():
            try:
                for f in (600, 450, 300):
                    winsound.Beep(f, 80)
            except Exception:
                pass

        if self.enabled:
            threading.Thread(target=_run, daemon=True, name="soundfx-gameover").start()
