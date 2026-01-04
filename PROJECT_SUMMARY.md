# 🎬 DoubleSub.io - Résumé du Projet

## Vue d'ensemble

**DoubleSub.io** est une application web pour fusionner des sous-titres bilingues, permettant d'apprendre les langues en regardant des films avec deux langues simultanément.

**Domaine acheté:** doublesub.io ✅

---

## 📁 Structure Complète du Projet

```
DoubleSub/
│
├── 📄 README.md                    # Documentation principale
├── 📄 QUICK_START.md               # Guide de démarrage rapide
├── 📄 DEPLOYMENT.md                # Guide de déploiement production
├── 📄 PROJECT_SUMMARY.md           # Ce fichier
│
├── 🔧 Configuration
│   ├── app.py                      # Application Flask principale (177 lignes)
│   ├── config.py                   # Configuration (35 lignes)
│   ├── wsgi.py                     # Point d'entrée WSGI pour production
│   ├── requirements.txt            # Dépendances Python
│   ├── .env.example                # Exemple de configuration environnement
│   └── .gitignore                  # Fichiers à ignorer par Git
│
├── 🚀 Scripts de lancement
│   ├── run_local.bat               # Lancement Windows
│   └── run_local.sh                # Lancement Linux/Mac
│
├── 🎨 Frontend
│   ├── templates/
│   │   └── index.html              # Interface utilisateur (234 lignes)
│   └── static/
│       ├── css/
│       │   └── style.css           # Styles modernes (549 lignes)
│       └── js/
│           └── app.js              # JavaScript frontend (307 lignes)
│
└── ⚙️ Backend
    └── utils/
        ├── __init__.py             # Module Python
        ├── subtitle_merger.py      # Logique de fusion SRT (242 lignes)
        └── ffmpeg_helper.py        # Extraction vidéo FFmpeg (109 lignes)
```

**Total:** ~1,650 lignes de code

---

## 🎯 Fonctionnalités

### ✅ Implémentées

1. **Upload de vidéos**
   - Formats supportés: MP4, MKV, AVI, MOV, WMV, FLV, WebM
   - Taille max: 500 MB
   - Extraction automatique des sous-titres avec FFmpeg

2. **Upload direct de SRT**
   - 2 fichiers SRT simultanés
   - Formats: SRT, ASS, SSA

3. **3 Modes de fusion**
   - **Tous**: Fusionne tous les sous-titres
   - **Chevauchements**: Uniquement les sous-titres qui se chevauchent
   - **Priorité**: Garde la langue 1 en priorité

4. **Configuration flexible**
   - Tolérance de timing ajustable (0-5000ms)
   - Mode de fusion sélectionnable

5. **Interface moderne**
   - Design responsive (mobile/desktop)
   - Drag & drop pour les fichiers
   - Animations fluides
   - Messages d'erreur clairs

6. **Sécurité**
   - Validation des types de fichiers
   - Limite de taille
   - Nettoyage automatique des fichiers temporaires

---

## 🛠️ Technologies Utilisées

### Backend
- **Python 3.8+** - Langage principal
- **Flask 3.0** - Framework web léger
- **Gunicorn** - Serveur WSGI pour production
- **FFmpeg** - Extraction et conversion de sous-titres

### Frontend
- **HTML5** - Structure sémantique
- **CSS3** - Design moderne avec gradients et animations
- **JavaScript Vanilla** - Pas de frameworks lourds
- **Fetch API** - Requêtes asynchrones

### Déploiement
- **Nginx** - Reverse proxy
- **Let's Encrypt** - SSL/HTTPS gratuit
- **Systemd** - Service Linux
- **Git** - Versioning

---

## 🚀 Installation et Lancement

### En Local (Test)

**Windows:**
```batch
run_local.bat
```

**Linux/Mac:**
```bash
chmod +x run_local.sh
./run_local.sh
```

Puis ouvrez: **http://localhost:5000**

### En Production

Voir [DEPLOYMENT.md](DEPLOYMENT.md) pour les instructions complètes.

Résumé:
```bash
# Installation
git clone <repo>
cd DoubleSub
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Lancement
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

---

## 📊 API Endpoints

### `POST /api/extract-subtitles`
Extrait les sous-titres d'une vidéo

**Body:** FormData avec `video` (fichier)

**Response:**
```json
{
  "success": true,
  "subtitles": [
    {
      "index": 2,
      "codec": "srt",
      "language": "eng",
      "title": "English"
    }
  ]
}
```

### `POST /api/merge`
Fusionne les sous-titres

**Body:** FormData avec:
- Mode vidéo: `video`, `primary_index`, `secondary_index`
- Mode SRT: `srt1`, `srt2`
- Commun: `mode`, `tolerance`

**Response:**
```json
{
  "success": true,
  "message": "Fusion réussie!",
  "output_file": "merged_xxx.srt",
  "cue_count": 1234
}
```

### `GET /download/<filename>`
Télécharge le fichier fusionné

**Response:** Fichier SRT

### `GET /health`
Health check

**Response:**
```json
{
  "status": "ok",
  "service": "doublesub.io"
}
```

---

## 🎨 Design et UX

### Palette de Couleurs
- **Primary:** #6366f1 (Indigo)
- **Secondary:** #8b5cf6 (Violet)
- **Success:** #10b981 (Vert)
- **Error:** #ef4444 (Rouge)
- **Background:** Dégradé de bleus foncés (#0f172a → #1e293b)

### Responsive Design
- Desktop: Layout en colonnes
- Mobile: Layout vertical adaptatif
- Breakpoint: 768px

### Animations
- Transitions fluides (0.3s)
- Progress bar animée
- Hover effects sur les boutons
- Drag & drop feedback visuel

---

## 🔒 Sécurité

1. **Validation des fichiers**
   - Type de fichier vérifié côté serveur
   - Taille limitée à 500 MB
   - Noms de fichiers sécurisés (secure_filename)

2. **Nettoyage automatique**
   - Cron job pour supprimer les fichiers > 24h
   - Pas de stockage permanent

3. **HTTPS**
   - Let's Encrypt (production)
   - Certificat SSL automatique

4. **Rate Limiting** (recommandé)
   - Nginx: 5 requêtes/minute par IP
   - Burst: 10 requêtes max

---

## 📈 Optimisations Possibles (Futures)

### Court terme
- [ ] Prévisualisation des sous-titres avant fusion
- [ ] Support de plus de langues (détection automatique)
- [ ] Personnalisation du style des sous-titres
- [ ] Historique des fusions récentes

### Moyen terme
- [ ] Compte utilisateur et sauvegarde
- [ ] Export en formats multiples (ASS, SSA, VTT)
- [ ] API publique avec clés
- [ ] Traduction automatique (Google Translate API)

### Long terme
- [ ] Application mobile (React Native)
- [ ] Extension navigateur
- [ ] Intégration avec services de streaming
- [ ] Machine learning pour alignement intelligent

---

## 📝 Maintenance

### Mise à jour du code
```bash
cd /var/www/doublesub
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart doublesub
```

### Voir les logs
```bash
# Application
sudo journalctl -u doublesub -f

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Backup
```bash
tar -czf doublesub-backup-$(date +%Y%m%d).tar.gz /var/www/doublesub
```

---

## 🎓 Code Réutilisable

Le code de fusion de sous-titres (`utils/subtitle_merger.py`) peut être réutilisé dans d'autres projets:

```python
from utils.subtitle_merger import SubtitleMerger

merger = SubtitleMerger()
result = merger.merge(
    'sub1.srt',
    'sub2.srt',
    'output.srt',
    mode='all',
    tolerance_ms=700
)
```

---

## 📞 Support

- **Email:** support@doublesub.io
- **GitHub:** Issues sur le repo
- **Documentation:** README.md, QUICK_START.md, DEPLOYMENT.md

---

## 📄 Licence

© 2025 DoubleSub.io - Tous droits réservés

---

**Projet créé le:** 3 janvier 2025
**Statut:** ✅ Prêt pour le déploiement
**Domaine:** doublesub.io (acheté)
