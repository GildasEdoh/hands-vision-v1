import math
import random
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np

from handvision.game.balloon import Balloon


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    color: Tuple[int, int, int]
    radius: float
    life: float
    max_life: float

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 320.0 * dt  # Gravité vers le bas
        self.vx *= (1.0 - 0.4 * dt)  # Friction de l'air
        self.life -= dt
        return self.life > 0.0


class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []

    def spawn_burst(
        self,
        center_x: float,
        center_y: float,
        color: Tuple[int, int, int],
        count: int = 16,
    ) -> None:
        for _ in range(count):
            angle = random.uniform(0.0, 2 * math.pi)
            speed = random.uniform(90.0, 320.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            radius = random.uniform(3.0, 7.0)
            max_life = random.uniform(0.35, 0.65)
            self.particles.append(
                Particle(
                    x=center_x,
                    y=center_y,
                    vx=vx,
                    vy=vy,
                    color=color,
                    radius=radius,
                    life=max_life,
                    max_life=max_life,
                )
            )

    def update(self, dt: float) -> None:
        self.particles = [p for p in self.particles if p.update(dt)]

    def draw(self, frame: np.ndarray) -> None:
        h, w = frame.shape[:2]
        for p in self.particles:
            ix, iy = int(p.x), int(p.y)
            if 0 <= ix < w and 0 <= iy < h:
                # Diminution progressive de la taille
                current_radius = max(1, int(p.radius * (p.life / p.max_life)))
                cv2.circle(frame, (ix, iy), current_radius, p.color, -1, lineType=cv2.LINE_AA)


@dataclass
class FloatingText:
    text: str
    x: float
    y: float
    color: Tuple[int, int, int]
    life: float = 0.8
    max_life: float = 0.8
    scale: float = 0.7

    def update(self, dt: float) -> bool:
        self.y -= 45.0 * dt
        self.life -= dt
        return self.life > 0.0

    def draw(self, frame: np.ndarray) -> None:
        alpha = max(0.0, min(1.0, self.life / self.max_life))
        ix, iy = int(self.x), int(self.y)
        # Ombre portée noire pour lisibilité
        cv2.putText(
            frame,
            self.text,
            (ix + 1, iy + 1),
            cv2.FONT_HERSHEY_DUPLEX,
            self.scale,
            (10, 10, 10),
            2,
            lineType=cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            self.text,
            (ix, iy),
            cv2.FONT_HERSHEY_DUPLEX,
            self.scale,
            self.color,
            2,
            lineType=cv2.LINE_AA,
        )


class VisualRenderer:
    """Renders game elements, laser crosshair, HUD, and pop animations."""

    def __init__(self):
        self.particle_system = ParticleSystem()
        self.floating_texts: List[FloatingText] = []

    def add_floating_text(
        self,
        text: str,
        x: float,
        y: float,
        color: Tuple[int, int, int] = (0, 255, 255),
        scale: float = 0.7,
    ) -> None:
        self.floating_texts.append(
            FloatingText(text=text, x=x, y=y, color=color, scale=scale)
        )

    def trigger_pop_effect(self, balloon: Balloon) -> None:
        # Particules de couleur du ballon + quelques étincelles blanches
        self.particle_system.spawn_burst(balloon.x, balloon.y, balloon.color, count=16)
        self.particle_system.spawn_burst(balloon.x, balloon.y, (255, 255, 255), count=6)
        
        # Texte flottant
        score_label = f"+{balloon.points}"
        text_color = (40, 230, 255) if balloon.is_golden else (255, 255, 255)
        self.add_floating_text(score_label, balloon.x - 20, balloon.y - 15, color=text_color)

    def update(self, dt: float) -> None:
        self.particle_system.update(dt)
        self.floating_texts = [t for t in self.floating_texts if t.update(dt)]

    def draw_balloon(self, frame: np.ndarray, balloon: Balloon) -> None:
        if not balloon.alive:
            return
        cx, cy = int(balloon.x), int(balloon.y)
        rx, ry = balloon.radius_x, balloon.radius_y

        # 1. Ficelle du ballon (ligne sinueuse)
        string_pts = [
            (cx, cy + ry),
            (cx - 4, cy + ry + 12),
            (cx + 4, cy + ry + 24),
            (cx, cy + ry + 36),
        ]
        cv2.polylines(
            frame,
            [np.array(string_pts, dtype=np.int32)],
            isClosed=False,
            color=(210, 210, 210),
            thickness=1,
            lineType=cv2.LINE_AA,
        )

        # 2. Noeud triangulaire à la base
        knot = np.array(
            [
                (cx - 5, cy + ry + 6),
                (cx + 5, cy + ry + 6),
                (cx, cy + ry),
            ],
            dtype=np.int32,
        )
        cv2.fillPoly(frame, [knot], balloon.color, lineType=cv2.LINE_AA)

        # 3. Corps du ballon (ellipse)
        cv2.ellipse(
            frame,
            (cx, cy),
            (rx, ry),
            0,
            0,
            360,
            balloon.color,
            -1,
            lineType=cv2.LINE_AA,
        )
        
        # Contour plus sombre pour faire ressortir
        contour_color = tuple(max(0, c - 50) for c in balloon.color)
        cv2.ellipse(
            frame,
            (cx, cy),
            (rx, ry),
            0,
            0,
            360,
            contour_color,
            2,
            lineType=cv2.LINE_AA,
        )

        # 4. Reflet spéculaire 3D (croissant blanc transparent en haut à gauche)
        highlight_x = cx - int(rx * 0.35)
        highlight_y = cy - int(ry * 0.35)
        cv2.ellipse(
            frame,
            (highlight_x, highlight_y),
            (max(2, int(rx * 0.22)), max(3, int(ry * 0.32))),
            -25,
            0,
            360,
            (255, 255, 255),
            -1,
            lineType=cv2.LINE_AA,
        )

        # 5. Effet scintillant si ballon doré
        if balloon.is_golden:
            for angle in (0, 90, 180, 270):
                rad = math.radians(angle + balloon.age * 90)
                sx = int(cx + math.cos(rad) * (rx + 8))
                sy = int(cy + math.sin(rad) * (ry + 8))
                cv2.circle(frame, (sx, sy), 2, (255, 255, 255), -1, lineType=cv2.LINE_AA)

    def draw_laser_crosshair(
        self,
        frame: np.ndarray,
        index_pos: Tuple[int, int],
        thumb_pos: Optional[Tuple[int, int]],
        is_pinched: bool,
        pinch_ratio: float,
    ) -> None:
        """
        Renders a futuristic laser crosshair at index tip, with pinch gauge line to thumb.
        """
        ix, iy = index_pos
        h, w = frame.shape[:2]

        # Ligne de guidage / tension entre pouce et index
        if thumb_pos is not None:
            tx, ty = thumb_pos
            # Couleur dynamique du vert (repos) au jaune puis rouge/cyan (proche du pincement)
            if is_pinched:
                line_color = (0, 255, 255)  # Jaune éclatant lors du tir
                thickness = 3
            else:
                # Interpolation vert -> rouge selon pinch_ratio (1.0 = repos, 0.0 = pincé)
                r = int(min(255, max(0, (1.0 - pinch_ratio) * 255)))
                g = int(min(255, max(0, pinch_ratio * 255)))
                line_color = (0, g, r)
                thickness = 2
            cv2.line(frame, (tx, ty), (ix, iy), line_color, thickness, lineType=cv2.LINE_AA)
            cv2.circle(frame, (tx, ty), 6, line_color, -1, lineType=cv2.LINE_AA)

        # Réticule de visée sur le bout de l'index
        base_color = (0, 255, 255) if is_pinched else (0, 240, 100)
        core_color = (255, 255, 255) if is_pinched else (0, 255, 120)
        radius = 24 if is_pinched else 18

        # Cercle extérieur
        cv2.circle(frame, (ix, iy), radius, base_color, 2, lineType=cv2.LINE_AA)

        # 4 mires de visée (crochets / repères cardinaux)
        notch = 6
        gap = 4
        # Haut
        cv2.line(frame, (ix, iy - radius - gap), (ix, iy - radius - gap - notch), base_color, 2, lineType=cv2.LINE_AA)
        # Bas
        cv2.line(frame, (ix, iy + radius + gap), (ix, iy + radius + gap + notch), base_color, 2, lineType=cv2.LINE_AA)
        # Gauche
        cv2.line(frame, (ix - radius - gap, iy), (ix - radius - gap - notch, iy), base_color, 2, lineType=cv2.LINE_AA)
        # Droite
        cv2.line(frame, (ix + radius + gap, iy), (ix + radius + gap + notch, iy), base_color, 2, lineType=cv2.LINE_AA)

        # Point central laser
        cv2.circle(frame, (ix, iy), 4, core_color, -1, lineType=cv2.LINE_AA)

        # Effet blast / onde de choc si pincé
        if is_pinched:
            cv2.circle(frame, (ix, iy), radius + 12, (0, 165, 255), 1, lineType=cv2.LINE_AA)

    def draw_hud(
        self,
        frame: np.ndarray,
        score: int,
        high_score: int,
        lives: int,
        combo: int,
        fps: float,
        time_elapsed: float,
    ) -> None:
        """Top glassmorphic banner displaying score, hearts, combo and fps."""
        h, w = frame.shape[:2]
        hud_height = 54

        # Bandeau semi-transparent
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, hud_height), (20, 22, 28), -1)
        cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)
        cv2.line(frame, (0, hud_height), (w, hud_height), (60, 65, 75), 1)

        # 1. Score
        score_text = f"SCORE: {score}"
        cv2.putText(
            frame,
            score_text,
            (18, 36),
            cv2.FONT_HERSHEY_DUPLEX,
            0.8,
            (255, 255, 255),
            2,
            lineType=cv2.LINE_AA,
        )

        # High score
        if high_score > 0:
            best_text = f"RECORD: {high_score}"
            cv2.putText(
                frame,
                best_text,
                (185, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 215, 255),
                1,
                lineType=cv2.LINE_AA,
            )

        # 2. Vies (Cœurs / badges)
        lives_x = w // 2 - 60
        cv2.putText(
            frame,
            "VIES:",
            (lives_x, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (200, 200, 200),
            1,
            lineType=cv2.LINE_AA,
        )
        for i in range(3):
            hx = lives_x + 65 + i * 26
            hy = 28
            # Si vie active : cercle plein rouge vif, sinon contour gris
            if i < lives:
                cv2.circle(frame, (hx, hy), 8, (60, 60, 245), -1, lineType=cv2.LINE_AA)
                cv2.circle(frame, (hx, hy), 8, (255, 255, 255), 1, lineType=cv2.LINE_AA)
            else:
                cv2.circle(frame, (hx, hy), 8, (70, 70, 80), 1, lineType=cv2.LINE_AA)

        # 3. Combo
        if combo > 1:
            combo_text = f"COMBO x{combo}!"
            combo_color = (0, 140, 255) if combo < 4 else (0, 60, 255)
            cv2.putText(
                frame,
                combo_text,
                (lives_x + 160, 36),
                cv2.FONT_HERSHEY_DUPLEX,
                0.7,
                combo_color,
                2,
                lineType=cv2.LINE_AA,
            )

        # 4. FPS & Temps à droite
        stat_text = f"FPS: {fps:.0f} | {time_elapsed:.0f}s"
        (tw, _), _ = cv2.getTextSize(stat_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.putText(
            frame,
            stat_text,
            (w - tw - 16, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (170, 175, 185),
            1,
            lineType=cv2.LINE_AA,
        )

        # Bandeau inférieur aide ergonomique
        footer_y = h - 14
        help_text = "Visez avec l'index | Pincez pouce+index pour tirer | 'R' Rejouer | 'Q' Quitter"
        (hw, _), _ = cv2.getTextSize(help_text, cv2.FONT_HERSHEY_SIMPLEX, 0.42, 1)
        # Fond discret
        cv2.putText(
            frame,
            help_text,
            ((w - hw) // 2, footer_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (210, 210, 210),
            1,
            lineType=cv2.LINE_AA,
        )

    def draw_game_over(
        self,
        frame: np.ndarray,
        final_score: int,
        high_score: int,
        replay_button_rect: Tuple[int, int, int, int],
        is_hovering_button: bool,
    ) -> None:
        """Game Over overlay with score summary and interactive replay button."""
        h, w = frame.shape[:2]
        # Voile sombre
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (15, 15, 20), -1)
        cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)

        # Titre Game Over
        title = "GAME OVER"
        (tw, th), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, 1.6, 3)
        cv2.putText(
            frame,
            title,
            ((w - tw) // 2, h // 3),
            cv2.FONT_HERSHEY_DUPLEX,
            1.6,
            (60, 60, 245),
            3,
            lineType=cv2.LINE_AA,
        )

        # Score final
        score_msg = f"Score final : {final_score}"
        (sw, _), _ = cv2.getTextSize(score_msg, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
        cv2.putText(
            frame,
            score_msg,
            ((w - sw) // 2, h // 3 + 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 255),
            2,
            lineType=cv2.LINE_AA,
        )

        # Record
        rec_msg = f"Meilleur score : {high_score}"
        (rw, _), _ = cv2.getTextSize(rec_msg, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
        cv2.putText(
            frame,
            rec_msg,
            ((w - rw) // 2, h // 3 + 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 215, 255),
            2,
            lineType=cv2.LINE_AA,
        )

        # Bouton virtuel "REJOUER"
        bx, by, bw, bh = replay_button_rect
        btn_color = (40, 190, 80) if is_hovering_button else (45, 130, 60)
        border_color = (120, 255, 150) if is_hovering_button else (200, 200, 200)

        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), btn_color, -1)
        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), border_color, 2)

        btn_text = "PINCER POUR REJOUER"
        (btw, bth), _ = cv2.getTextSize(btn_text, cv2.FONT_HERSHEY_DUPLEX, 0.7, 2)
        cv2.putText(
            frame,
            btn_text,
            (bx + (bw - btw) // 2, by + (bh + bth) // 2),
            cv2.FONT_HERSHEY_DUPLEX,
            0.7,
            (255, 255, 255),
            2,
            lineType=cv2.LINE_AA,
        )

        # Raccourci clavier de secours
        sub_text = "ou appuyez sur la touche 'R'"
        (stw, _), _ = cv2.getTextSize(sub_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.putText(
            frame,
            sub_text,
            ((w - stw) // 2, by + bh + 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (180, 180, 180),
            1,
            lineType=cv2.LINE_AA,
        )

    def draw_start_screen(
        self,
        frame: np.ndarray,
        play_button_rect: Tuple[int, int, int, int],
        is_hovering_button: bool,
    ) -> None:
        """Initial welcome overlay explaining rules."""
        h, w = frame.shape[:2]
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, h), (18, 20, 26), -1)
        cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)

        title = "BALLOON POPPER VISION"
        (tw, _), _ = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, 1.4, 3)
        cv2.putText(
            frame,
            title,
            ((w - tw) // 2, h // 4),
            cv2.FONT_HERSHEY_DUPLEX,
            1.4,
            (0, 220, 255),
            3,
            lineType=cv2.LINE_AA,
        )

        # Instructions illustrées
        rules = [
            "- Pointez le bout de l'index pour viser les ballons.",
            "- Rapprochez le pouce et l'index (pincement) pour tirer !",
            "- Faites eclater les ballons avant qu'ils ne s'echappent.",
            "- Attention aux ballons dores qui rapportent un bonus !",
        ]
        start_y = h // 4 + 60
        for i, rule in enumerate(rules):
            cv2.putText(
                frame,
                rule,
                (w // 2 - 260, start_y + i * 36),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (240, 240, 240),
                1,
                lineType=cv2.LINE_AA,
            )

        # Bouton virtuel "JOUER"
        bx, by, bw, bh = play_button_rect
        btn_color = (0, 170, 255) if is_hovering_button else (0, 120, 210)
        border_color = (180, 230, 255) if is_hovering_button else (220, 220, 220)

        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), btn_color, -1)
        cv2.rectangle(frame, (bx, by), (bx + bw, by + bh), border_color, 2)

        btn_text = "PINCER POUR COMMENCER"
        (btw, bth), _ = cv2.getTextSize(btn_text, cv2.FONT_HERSHEY_DUPLEX, 0.7, 2)
        cv2.putText(
            frame,
            btn_text,
            (bx + (bw - btw) // 2, by + (bh + bth) // 2),
            cv2.FONT_HERSHEY_DUPLEX,
            0.7,
            (255, 255, 255),
            2,
            lineType=cv2.LINE_AA,
        )
