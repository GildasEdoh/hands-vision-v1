import math
import unittest
from unittest.mock import MagicMock

import numpy as np

from handvision.interfaces import Landmark
from handvision.game.balloon import Balloon
from handvision.game.target_manager import TargetManager
from handvision.game.game_engine import GameEngine, GameState
from handvision.game.module import BalloonShooterGameModule


def make_dummy_landmarks(index_x: float, index_y: float, thumb_x: float, thumb_y: float):
    """Generates a 21-landmark list placing index tip at (index_x, index_y) and thumb tip at (thumb_x, thumb_y)."""
    landmarks = []
    for i in range(21):
        if i == 8:
            landmarks.append(Landmark(x_=index_x, y_=index_y, z_=0.0, visibility=1.0, presence=None, name=None))
        elif i == 4:
            landmarks.append(Landmark(x_=thumb_x, y_=thumb_y, z_=0.0, visibility=1.0, presence=None, name=None))
        elif i == 0:
            # Poignet
            landmarks.append(Landmark(x_=0.5, y_=0.8, z_=0.0, visibility=1.0, presence=None, name=None))
        elif i == 9:
            # Base du majeur
            landmarks.append(Landmark(x_=0.5, y_=0.5, z_=0.0, visibility=1.0, presence=None, name=None))
        else:
            landmarks.append(Landmark(x_=0.5, y_=0.5, z_=0.0, visibility=1.0, presence=None, name=None))
    return landmarks


class BalloonTests(unittest.TestCase):
    def test_balloon_creation_and_movement(self):
        b = Balloon(
            id=1,
            x=200.0,
            y=300.0,
            base_x=200.0,
            radius_x=30,
            radius_y=40,
            speed_y=100.0,
            oscillation_amplitude=0.0,  # Pas d'oscillation pour ce test direct
            oscillation_speed=1.0,
            phase=0.0,
        )
        b.update(0.5)
        # y doit diminuer de 100 * 0.5 = 50px (il monte)
        self.assertAlmostEqual(b.y, 250.0, delta=0.1)
        self.assertFalse(b.is_offscreen())

    def test_balloon_is_hit(self):
        b = Balloon(
            id=2,
            x=100.0,
            y=100.0,
            base_x=100.0,
            radius_x=30,
            radius_y=30,
        )
        # Directement au centre
        self.assertTrue(b.is_hit(100.0, 100.0))
        # À la limite du rayon
        self.assertTrue(b.is_hit(125.0, 100.0))
        # Très loin
        self.assertFalse(b.is_hit(200.0, 200.0))

    def test_balloon_offscreen_detection(self):
        b = Balloon(
            id=3,
            x=100.0,
            y=-50.0,
            base_x=100.0,
            radius_x=30,
            radius_y=40,
        )
        # y + radius_y = -50 + 40 = -10 < 0 -> offscreen
        self.assertTrue(b.is_offscreen())


class TargetManagerTests(unittest.TestCase):
    def test_target_manager_hit_detection(self):
        tm = TargetManager(max_balloons=3)
        b1 = Balloon(id=1, x=100.0, y=100.0, base_x=100.0, radius_x=30, radius_y=30)
        b2 = Balloon(id=2, x=400.0, y=400.0, base_x=400.0, radius_x=30, radius_y=30)
        tm.balloons = [b1, b2]

        # Tir sur b1
        hit = tm.check_hit(105.0, 105.0)
        self.assertIsNotNone(hit)
        self.assertEqual(hit.id, 1)
        self.assertNotIn(b1, tm.balloons)
        self.assertIn(b2, tm.balloons)

        # Tir dans le vide
        miss = tm.check_hit(200.0, 200.0)
        self.assertIsNone(miss)

    def test_target_manager_escaped_balloons(self):
        tm = TargetManager()
        b_escaped = Balloon(id=1, x=100.0, y=-60.0, base_x=100.0, radius_x=20, radius_y=20)
        b_alive = Balloon(id=2, x=200.0, y=200.0, base_x=200.0, radius_x=20, radius_y=20, speed_y=0.0)
        tm.balloons = [b_escaped, b_alive]

        escaped = tm.update(0.01, 640, 480)
        self.assertEqual(len(escaped), 1)
        self.assertEqual(escaped[0].id, 1)
        self.assertIn(b_alive, tm.balloons)


class GameEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(sound_enabled=False)

    def test_state_flow_and_button_interaction(self):
        self.assertEqual(self.engine.state, GameState.START)
        bx, by, bw, bh = self.engine.get_button_rect(640, 480)
        
        # Tir sur le bouton virtuel "JOUER"
        self.engine.handle_shot(bx + bw // 2, by + bh // 2, 640, 480)
        self.assertEqual(self.engine.state, GameState.PLAYING)
        self.assertEqual(self.engine.score, 0)
        self.assertEqual(self.engine.lives, 3)

    def test_score_and_combo_accumulation(self):
        self.engine.start_game()
        # On injecte manuellement deux ballons
        b1 = Balloon(id=1, x=150.0, y=150.0, base_x=150.0, radius_x=30, radius_y=30, points=10)
        b2 = Balloon(id=2, x=250.0, y=250.0, base_x=250.0, radius_x=30, radius_y=30, points=10)
        self.engine.target_manager.balloons = [b1, b2]

        # Premier tir
        self.engine.handle_shot(150.0, 150.0, 640, 480)
        self.assertEqual(self.engine.score, 10)
        self.assertEqual(self.engine.combo, 1)

        # Deuxième tir immédiat (combo)
        self.engine.handle_shot(250.0, 250.0, 640, 480)
        # points = 10 * 1.5 = 15 -> score total = 25
        self.assertEqual(self.engine.score, 25)
        self.assertEqual(self.engine.combo, 2)

    def test_game_over_when_lives_exhausted(self):
        self.engine.start_game()
        self.engine.lives = 1
        # Simuler un ballon qui s'échappe
        escaped_balloon = Balloon(id=1, x=100.0, y=-50.0, base_x=100.0, radius_y=20)
        self.engine.target_manager.balloons = [escaped_balloon]

        self.engine.update(0.1, 640, 480)
        self.assertEqual(self.engine.lives, 0)
        self.assertEqual(self.engine.state, GameState.GAME_OVER)


class BalloonShooterGameModuleTests(unittest.TestCase):
    def setUp(self):
        self.module = BalloonShooterGameModule(sound_enabled=False)

    def test_process_frame_without_hand(self):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        processed = self.module.process_frame(frame, [], fps=30.0, elapsed_seconds=1.0)
        self.assertEqual(processed.shape, (480, 640, 3))

    def test_pinch_detection_triggers_shot(self):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.module.engine.start_game()
        
        # Placer un ballon à (300, 200)
        target = Balloon(id=1, x=300.0, y=200.0, base_x=300.0, radius_x=30, radius_y=30, points=10)
        self.module.engine.target_manager.balloons = [target]

        # 1. Main détendue : index à (300, 200) et pouce à (300, 300) -> distance = 100px > seuil
        norm_ix = 300 / 640
        norm_iy = 200 / 480
        norm_tx = 300 / 640
        norm_ty = 300 / 480
        relaxed_hand = make_dummy_landmarks(norm_ix, norm_iy, norm_tx, norm_ty)
        self.module.process_frame(frame, relaxed_hand, fps=30.0, elapsed_seconds=0.1)
        self.assertEqual(self.module.engine.score, 0)
        self.assertIn(target, self.module.engine.target_manager.balloons)

        # 2. Main pincée : pouce et index très proches à (300, 200) -> distance < seuil
        pinched_hand = make_dummy_landmarks(norm_ix, norm_iy, norm_ix + 0.01, norm_iy + 0.01)
        self.module.process_frame(frame, pinched_hand, fps=30.0, elapsed_seconds=0.2)

        # Le tir doit avoir détruit le ballon
        self.assertEqual(self.module.engine.score, 10)
        self.assertNotIn(target, self.module.engine.target_manager.balloons)

    def test_keyboard_shortcuts(self):
        self.module.engine.state = GameState.GAME_OVER
        self.module.handle_key(ord("r"))
        self.assertEqual(self.module.engine.state, GameState.PLAYING)


if __name__ == "__main__":
    unittest.main()
