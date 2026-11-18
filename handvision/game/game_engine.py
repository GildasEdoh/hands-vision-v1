from enum import Enum, auto
import time
from typing import Optional, Tuple

import cv2
import numpy as np

from handvision.game.balloon import Balloon
from handvision.game.sound import SoundFX
from handvision.game.target_manager import TargetManager
from handvision.game.visual_effects import VisualRenderer


class GameState(Enum):
    START = auto()
    PLAYING = auto()
    GAME_OVER = auto()


class GameEngine:
    """Core game mechanics, score tracking, state machine, and audio-visual feedback."""

    def __init__(self, sound_enabled: bool = True):
        self.state: GameState = GameState.START
        self.score: int = 0
        self.high_score: int = 0
        self.lives: int = 3
        self.combo: int = 0
        self.last_hit_time: float = 0.0
        self.total_time: float = 0.0

        self.target_manager = TargetManager()
        self.renderer = VisualRenderer()
        self.sound = SoundFX(enabled=sound_enabled)

    def get_button_rect(self, screen_width: int, screen_height: int) -> Tuple[int, int, int, int]:
        """Returns (x, y, width, height) of the interactive start/replay button."""
        btn_width = 340
        btn_height = 60
        btn_x = (screen_width - btn_width) // 2
        btn_y = int(screen_height * 0.62)
        return (btn_x, btn_y, btn_width, btn_height)

    def is_inside_button(self, point_x: float, point_y: float, screen_width: int, screen_height: int) -> bool:
        bx, by, bw, bh = self.get_button_rect(screen_width, screen_height)
        return bx <= point_x <= (bx + bw) and by <= point_y <= (by + bh)

    def start_game(self) -> None:
        self.score = 0
        self.lives = 3
        self.combo = 0
        self.total_time = 0.0
        self.target_manager.clear()
        self.state = GameState.PLAYING
        self.sound.play_pop(pitch_mult=1.3)

    def handle_shot(self, shot_x: float, shot_y: float, screen_width: int, screen_height: int) -> None:
        """Processes a pinch-shot event at coordinates (shot_x, shot_y)."""
        now = time.monotonic()

        if self.state in (GameState.START, GameState.GAME_OVER):
            # Vérifier si l'utilisateur tire sur le bouton virtuel
            if self.is_inside_button(shot_x, shot_y, screen_width, screen_height):
                self.start_game()
            return

        if self.state == GameState.PLAYING:
            hit_balloon = self.target_manager.check_hit(shot_x, shot_y)
            if hit_balloon is not None:
                # Calcul du combo (moins de 1.8s entre deux tirs réussis)
                if now - self.last_hit_time <= 1.8:
                    self.combo += 1
                else:
                    self.combo = 1
                self.last_hit_time = now

                # Calcul des points avec multiplicateur combo
                multiplier = 1 + (self.combo - 1) * 0.5
                points_awarded = int(hit_balloon.points * multiplier)
                self.score += points_awarded
                if self.score > self.high_score:
                    self.high_score = self.score

                # Effets visuels & sonores
                self.renderer.trigger_pop_effect(hit_balloon)
                if self.combo > 1:
                    self.renderer.add_floating_text(
                        f"COMBO x{self.combo}!",
                        hit_balloon.x - 30,
                        hit_balloon.y - 45,
                        color=(0, 215, 255),
                        scale=0.8,
                    )

                if hit_balloon.is_golden:
                    self.sound.play_golden_pop()
                else:
                    pitch = min(1.8, 1.0 + (self.combo - 1) * 0.1)
                    self.sound.play_pop(pitch_mult=pitch)

                self.target_manager.update_difficulty(self.score)
            else:
                # Tir dans le vide : réinitialisation du combo
                if self.combo > 0:
                    self.combo = 0
                self.sound.play_miss()

    def update(self, dt: float, screen_width: int, screen_height: int) -> None:
        """Advance game physics and state."""
        self.renderer.update(dt)

        if self.state == GameState.PLAYING:
            self.total_time += dt
            escaped = self.target_manager.update(dt, screen_width, screen_height)
            for balloon in escaped:
                self.lives -= 1
                self.combo = 0
                self.renderer.add_floating_text(
                    "-1 VIE",
                    balloon.x - 25,
                    30,
                    color=(50, 50, 255),
                    scale=0.8,
                )

            if self.lives <= 0:
                self.lives = 0
                self.state = GameState.GAME_OVER
                self.sound.play_game_over()

    def render(
        self,
        frame: np.ndarray,
        fps: float,
        cursor_pos: Optional[Tuple[int, int]],
        thumb_pos: Optional[Tuple[int, int]],
        is_pinched: bool,
        pinch_ratio: float,
    ) -> np.ndarray:
        """Render complete game layer onto the webcam frame."""
        h, w = frame.shape[:2]
        btn_rect = self.get_button_rect(w, h)
        is_hovering_btn = False
        if cursor_pos is not None:
            is_hovering_btn = self.is_inside_button(cursor_pos[0], cursor_pos[1], w, h)

        if self.state == GameState.START:
            self.renderer.draw_start_screen(frame, btn_rect, is_hovering_btn)
        elif self.state == GameState.PLAYING:
            # 1. Dessiner les ballons actifs
            for b in self.target_manager.balloons:
                self.renderer.draw_balloon(frame, b)

            # 2. Dessiner les particules et textes flottants
            self.renderer.particle_system.draw(frame)
            for t in self.renderer.floating_texts:
                t.draw(frame)

            # 3. HUD
            self.renderer.draw_hud(
                frame,
                score=self.score,
                high_score=self.high_score,
                lives=self.lives,
                combo=self.combo,
                fps=fps,
                time_elapsed=self.total_time,
            )
        elif self.state == GameState.GAME_OVER:
            # Particules résiduelles
            self.renderer.particle_system.draw(frame)
            for t in self.renderer.floating_texts:
                t.draw(frame)

            self.renderer.draw_game_over(
                frame,
                final_score=self.score,
                high_score=self.high_score,
                replay_button_rect=btn_rect,
                is_hovering_button=is_hovering_btn,
            )

        # 4. Réticule laser si la main est détectée
        if cursor_pos is not None:
            self.renderer.draw_laser_crosshair(
                frame,
                index_pos=cursor_pos,
                thumb_pos=thumb_pos,
                is_pinched=is_pinched,
                pinch_ratio=pinch_ratio,
            )
        else:
            # Message incitatif si aucune main n'est visible
            no_hand_msg = "Levez la main pour viser"
            (mw, _), _ = cv2.getTextSize(no_hand_msg, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            cv2.putText(
                frame,
                no_hand_msg,
                ((w - mw) // 2, h - 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (120, 220, 255),
                1,
                lineType=cv2.LINE_AA,
            )

        return frame
