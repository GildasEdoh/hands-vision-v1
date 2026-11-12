# Hands Vision

Hands Vision est un projet expérimental de vision par ordinateur qui vise à
permettre d'interagir avec un ordinateur à l'aide des mains, sans contact.
L'objectif est de construire le projet progressivement : une base commune de
suivi des mains, puis plusieurs expériences indépendantes que l'on pourra
lancer et faire évoluer séparément.

## Objectifs

- Détecter et suivre les mains à partir d'une webcam.
- Réutiliser ce suivi dans plusieurs expériences indépendantes.
- Garder chaque expérience suffisamment isolée pour pouvoir la développer,
  tester et lancer sans affecter les autres.
- Ajouter des fonctionnalités au fil du temps, par exemple :
  - **Coloriage sans contact** : sélectionner une couleur et remplir une zone
    en approchant un doigt de cette zone à l'écran.
  - **Dessin vers texte** : interpréter un dessin réalisé par l'utilisateur
    et proposer une transcription textuelle.

Ces fonctionnalités sont des objectifs, pas des fonctions déjà disponibles.

## État actuel

Le prototype actuel, dans `main.py`, ouvre la webcam, détecte jusqu'à deux
mains avec MediaPipe, affiche les repères des mains et imprime les coordonnées
du bout de l'index. Il s'agit du point de départ du projet ; il n'est pas encore
réparti dans la nouvelle architecture.

Le modèle MediaPipe `hand_landmarker.task` doit rester disponible à la racine
pour ce prototype. Le dossier `assets/models/` est prévu pour accueillir les
modèles quand le code sera organisé autour du nouveau paquet.

## Architecture cible

```text
hands-vision-v1/
├── handvision/
│   ├── __init__.py
│   ├── core/
│   │   └── __init__.py
│   ├── vision/
│   │   └── __init__.py
│   ├── interfaces/
│   │   └── __init__.py
│   └── modules/
│       ├── __init__.py
│       ├── coloring/
│       │   └── __init__.py
│       └── drawing_to_text/
│           └── __init__.py
├── assets/
│   └── models/
│       └── .gitkeep
├── tests/
│   └── .gitkeep
├── main.py
├── hand_landmarker.task
└── Readme.md
```

### Rôle des dossiers

- `handvision/core/` : éléments communs aux expériences, tels que la
  configuration et les données partagées.
- `handvision/vision/` : capture vidéo, détection des mains et traitement des
  repères.
- `handvision/interfaces/` : interactions avec les entrées et sorties,
  notamment les fenêtres et les commandes utilisateur.
- `handvision/modules/` : expériences autonomes. Chaque fonctionnalité possède
  son propre sous-dossier et pourra avoir son propre point de lancement.
- `assets/models/` : modèles nécessaires aux fonctionnalités du projet.
- `tests/` : tests automatisés, à ajouter avec les premiers composants.
- `main.py` : point d'entrée historique du prototype actuel, conservé pendant
  la transition.

Les fichiers `__init__.py` posent les frontières des paquets Python. Les
nouveaux modules ne sont pas encore implémentés ni exécutables : leurs points
d'entrée seront ajoutés lorsqu'une première fonctionnalité sera développée.

## Prérequis

- Python 3, dans une version compatible avec MediaPipe et OpenCV.
- Une webcam accessible depuis l'ordinateur.
- Les bibliothèques OpenCV et MediaPipe.
- Le fichier de modèle `hand_landmarker.task` à la racine pour le prototype
  actuel.

## Lancer le prototype actuel

Depuis la racine du dépôt, installer les dépendances si nécessaire, puis lancer
le point d'entrée existant :

```powershell
python -m pip install opencv-python mediapipe
python main.py
```

La fenêtre vidéo se ferme avec la touche `Q`. Si la webcam n'est pas accessible
ou si le modèle est absent, vérifier les permissions caméra et la présence du
fichier `hand_landmarker.task`.

## Développement progressif

1. Stabiliser la capture vidéo et le suivi des mains dans les composants
   communs.
2. Créer le premier module d'expérience dans son dossier dédié.
3. Ajouter à ce module un point de lancement indépendant et documenter sa
   commande ici.
4. Ajouter des tests pour les comportements qui peuvent être vérifiés sans
   webcam.
5. Répéter cette démarche pour les expériences suivantes, sans coupler leur
   logique entre elles.

Lorsqu'un module sera prêt, sa méthode de lancement, ses dépendances propres et
ses limites devront être documentées dans cette page.
