#!/usr/bin/env python3
"""
Point d'entree principal du mini-jeu interactif Balloon Popper Vision.

Controle :
- Visez avec le bout de l'index (Landmark #8)
- Pincez le pouce et l'index (Landmarks #4 & #8) pour declencher le tir
- Faites eclater les ballons avant qu'ils ne sortent de l'ecran
- Visez et pincez sur le bouton "JOUER / REJOUER" ou appuyez sur 'R' pour recommencer
- Appuyez sur 'Q' ou 'Echap' pour quitter
- Appuyez sur 'H' pour afficher/masquer le squelette de la main
- Appuyez sur 'S' pour activer/couper le son
"""

import argparse
import logging
import sys

from handvision.game import BalloonShooterGameModule
from handvision.vision import StreamCaptureManager


def parse_args():
    parser = argparse.ArgumentParser(
        description="Jeu de tir de ballons par vision par ordinateur et MediaPipe"
    )
    parser.add_argument(
        "--source",
        default=0,
        help="Index de la webcam (defaut: 0) ou chemin vers un fichier video",
    )
    parser.add_argument(
        "--no-sound",
        action="store_true",
        help="Desactiver les effets sonores",
    )
    parser.add_argument(
        "--skeleton",
        action="store_true",
        help="Afficher le squelette de la main en surimpression",
    )
    parser.add_argument(
        "--pinch-threshold",
        type=float,
        default=38.0,
        help="Seuil de distance en pixels pour detecter le pincement (defaut: 38.0)",
    )
    parser.add_argument(
        "--no-flip",
        action="store_true",
        help="Ne pas inverser l'image en miroir horizontal",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("BalloonShooter")

    args = parse_args()

    # Si --source est un entier (ex: "0", "1"), le convertir en int pour OpenCV
    try:
        source = int(args.source)
    except ValueError:
        source = args.source

    logger.info("Initialisation du module de jeu Balloon Popper...")
    game_module = BalloonShooterGameModule(
        sound_enabled=not args.no_sound,
        base_pinch_threshold=args.pinch_threshold,
        show_skeleton=args.skeleton,
    )

    logger.info("Lancement du flux webcam via StreamCaptureManager...")
    manager = StreamCaptureManager(
        module=game_module,
        window_title="Hand Vision - Balloon Shooter Game",
    )

    try:
        manager.run(source=source, flip=not args.no_flip)
    except Exception as exc:
        logger.error(f"Erreur lors de l'execution du jeu : {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
