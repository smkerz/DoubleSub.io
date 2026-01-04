# DoubleSub.io - Bilingual Subtitle Merger

🎬 **Fusionnez vos sous-titres en dual-langue pour un apprentissage optimal des langues!**

## Fonctionnalités

- ✅ Upload de fichiers vidéo (extraction automatique des sous-titres)
- ✅ Upload direct de 2 fichiers SRT
- ✅ Fusion intelligente en dual-langue (haut/bas)
- ✅ Mode de fusion configurable (tous, chevauchements, priorité)
- ✅ Téléchargement du fichier SRT fusionné
- ✅ Interface moderne et responsive

## Stack Technique

- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Backend**: Python 3.8+ avec Flask
- **Processing**: FFmpeg pour extraction vidéo
- **Déploiement**: Compatible avec tout serveur Python (Gunicorn, uWSGI)

## Installation

### Prérequis

```bash
# Python 3.8+
python --version

# FFmpeg
ffmpeg -version
```

### Installation des dépendances

```bash
pip install -r requirements.txt
```

### Lancer en développement

```bash
python app.py
```

Le site sera accessible sur `http://localhost:5000`

### Déploiement en production

```bash
# Avec Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Ou avec uWSGI
uwsgi --http :5000 --wsgi-file app.py --callable app
```

## Configuration

Éditez `config.py` pour personnaliser:
- Port du serveur
- Taille max des uploads
- Dossiers temporaires
- etc.

## Structure du Projet

```
DoubleSub/
├── app.py                 # Application Flask principale
├── config.py              # Configuration
├── requirements.txt       # Dépendances Python
├── static/
│   ├── css/
│   │   └── style.css     # Styles CSS
│   ├── js/
│   │   └── app.js        # JavaScript frontend
│   └── images/
│       └── logo.png      # Logo du site
├── templates/
│   └── index.html        # Page HTML principale
├── utils/
│   ├── subtitle_merger.py  # Logique de fusion
│   └── ffmpeg_helper.py    # Extraction vidéo
└── uploads/              # Dossier temporaire (auto-généré)
```

## Licence

© 2025 DoubleSub.io - Tous droits réservés
