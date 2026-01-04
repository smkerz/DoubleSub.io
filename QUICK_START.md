# DoubleSub.io - Démarrage Rapide 🚀

## Test en Local (Windows)

1. **Double-cliquez sur `run_local.bat`**
   - Le script va installer tout automatiquement
   - Le site s'ouvrira sur http://localhost:5000

2. **Ouvrez votre navigateur**: http://localhost:5000

C'est tout! 🎉

## Test en Local (Linux/Mac)

```bash
chmod +x run_local.sh
./run_local.sh
```

Puis ouvrez: http://localhost:5000

## Utilisation

### Mode 1: Upload Vidéo
1. Cliquez sur "Upload Vidéo"
2. Glissez votre fichier vidéo (MP4, MKV, etc.)
3. Sélectionnez 2 sous-titres de la liste
4. Cliquez sur "Fusionner"
5. Téléchargez le fichier SRT fusionné

### Mode 2: Upload SRT Direct
1. Cliquez sur "Upload SRT"
2. Upload 2 fichiers SRT séparés
3. Cliquez sur "Fusionner"
4. Téléchargez le résultat

## Fonctionnalités

✅ **Upload vidéo** - Extraction automatique des sous-titres
✅ **Upload SRT** - Fusion directe de 2 fichiers SRT
✅ **3 modes de fusion**:
   - Tous les sous-titres
   - Chevauchements uniquement
   - Priorité à la langue 1
✅ **Tolérance configurable** - Ajustez le timing
✅ **Interface moderne** - Design responsive et élégant
✅ **Drag & Drop** - Glissez-déposez vos fichiers

## Structure du Projet

```
DoubleSub/
├── app.py                    # Application Flask
├── config.py                 # Configuration
├── requirements.txt          # Dépendances Python
├── templates/
│   └── index.html           # Interface utilisateur
├── static/
│   ├── css/style.css        # Styles
│   └── js/app.js            # JavaScript
├── utils/
│   ├── subtitle_merger.py   # Logique de fusion
│   └── ffmpeg_helper.py     # Extraction vidéo
└── uploads/                 # Fichiers temporaires
```

## Prérequis

- **Python 3.8+** (pour le backend)
- **FFmpeg** (optionnel, pour extraction depuis vidéo)

### Installer FFmpeg

**Windows:**
1. Téléchargez: https://ffmpeg.org/download.html
2. Ajoutez au PATH système

**Linux:**
```bash
sudo apt install ffmpeg
```

**Mac:**
```bash
brew install ffmpeg
```

## Déploiement sur Serveur

Voir le fichier [DEPLOYMENT.md](DEPLOYMENT.md) pour les instructions complètes.

Résumé rapide:
```bash
# Sur votre serveur
git clone <votre-repo>
cd DoubleSub
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

Puis configurez Nginx comme reverse proxy.

## Configuration

Créez un fichier `.env` (copiez depuis `.env.example`):
```
SECRET_KEY=votre-cle-secrete
DEBUG=True
```

## Problèmes Courants

### "Module not found"
```bash
pip install -r requirements.txt
```

### "FFmpeg not found"
Installez FFmpeg ou utilisez uniquement le mode "Upload SRT"

### Port 5000 déjà utilisé
Changez le port dans `.env`:
```
PORT=8000
```

## Support

- 📧 Email: support@doublesub.io
- 🐛 Issues: [GitHub Issues](https://github.com/votre-repo/issues)

## Licence

© 2025 DoubleSub.io
