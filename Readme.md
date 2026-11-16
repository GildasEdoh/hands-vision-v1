# Hands Vision

Hands Vision est une application Python de vision par ordinateur. Elle partage
un pipeline webcam et MediaPipe entre des modules d'expérience indépendants.
Le premier module contrôle le volume système Windows avec des gestes de la main.
Les expériences de coloriage et de dessin vers texte restent à développer.

## Prérequis

- Python compatible avec les versions installées de MediaPipe et OpenCV.
- Une webcam accessible.
- Windows pour contrôler le volume système.
- Le modèle `hand_landmarker.task` à la racine du dépôt.

Installez les dépendances du projet puis lancez l'application depuis la racine :

```powershell
python -m pip install -r requirements.txt
python main.py
```

Appuyez sur `Q` ou `Échap` pour quitter. L'application signale explicitement
si la webcam ou le modèle ne peut pas être ouvert.

## Module de contrôle du volume

Le volume est réglé à l'aide du volume principal de Windows :

1. Touchez l'icône de volume en haut à droite avec le bout de l'index pour
   afficher ou masquer la barre.
2. Variez l'écartement entre le **pouce et l'index** : rapprochez-les pour
   diminuer le volume et éloignez-les pour l'augmenter. Il n'est pas nécessaire
   de placer les doigts sur la barre.

La barre verticale affiche le niveau, mais sa position ne contrôle pas le
volume. Les instructions et le pourcentage restent dans un panneau séparé.

## Organisation actuelle

```text
handvision/
├── core/
│   └── timing.py
├── detection/
│   └── mediapipe_detector.py
├── interfaces/
│   └── land_mark.py
├── modules/
│   ├── base.py
│   └── volume_control/
│       ├── audio.py
│       ├── gesture.py
│       └── module.py
├── my_utils/
│   ├── detections_metrics.py
│   ├── extract_land_mark.py
│   └── land_mark_draw.py
└── vision/
    ├── draw_manager.py
    ├── frame_queue.py
    └── stream_capture_manager.py
```

- `core/` fournit les utilitaires indépendants des périphériques, notamment
  l'horloge monotone requise par MediaPipe en mode vidéo.
- `detection/` encapsule le modèle MediaPipe et sa durée de vie.
- `vision/` orchestre la capture, le traitement asynchrone et l'affichage.
- `my_utils/` contient les conversions de repères et les métriques.
- `modules/base.py` définit le contrat partagé des expériences.
- `modules/volume_control/` sépare le geste, le contrôle audio Windows et
  l'affichage du module de volume.

Les files de capture et de résultat ne conservent que l'image la plus récente :
les images en attente sont remplacées plutôt que de laisser s'accumuler un
retard. Les mesures de temps de file, détection, dessin et affichage sont
résumées dans les journaux à l'arrêt.

## Développement et tests

Les tests automatisés ne nécessitent pas de webcam :

```powershell
python -m unittest discover -s tests
```

Pour ajouter une expérience, implémentez `VisionModule.process_frame` et
`close`, puis passez cette instance au `StreamCaptureManager`. La capture, la
détection, le dessin commun des repères et l'arrêt restent gérés par le pipeline
partagé.
