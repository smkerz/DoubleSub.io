# Guide de Déploiement - DoubleSub.io

## Prérequis sur le serveur

1. **Python 3.8+**
```bash
python3 --version
```

2. **FFmpeg et FFprobe**
```bash
sudo apt update
sudo apt install ffmpeg
ffmpeg -version
```

3. **Nginx** (optionnel, recommandé pour la production)
```bash
sudo apt install nginx
```

## Installation

### 1. Cloner le projet
```bash
cd /var/www/
git clone <votre-repo> doublesub
cd doublesub
```

### 2. Créer un environnement virtuel
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4. Créer les dossiers nécessaires
```bash
mkdir -p uploads
chmod 755 uploads
```

### 5. Configuration
Créez un fichier `.env`:
```bash
nano .env
```

Contenu:
```
SECRET_KEY=votre-cle-secrete-ultra-securisee-ici
DEBUG=False
```

## Déploiement avec Gunicorn

### 1. Test en local
```bash
gunicorn -w 4 -b 127.0.0.1:5000 wsgi:app
```

### 2. Créer un service systemd
```bash
sudo nano /etc/systemd/system/doublesub.service
```

Contenu:
```ini
[Unit]
Description=DoubleSub.io Gunicorn Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/doublesub
Environment="PATH=/var/www/doublesub/venv/bin"
ExecStart=/var/www/doublesub/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 wsgi:app

[Install]
WantedBy=multi-user.target
```

### 3. Activer et démarrer le service
```bash
sudo systemctl daemon-reload
sudo systemctl enable doublesub
sudo systemctl start doublesub
sudo systemctl status doublesub
```

## Configuration Nginx (Reverse Proxy)

```bash
sudo nano /etc/nginx/sites-available/doublesub.io
```

Contenu:
```nginx
server {
    listen 80;
    server_name doublesub.io www.doublesub.io;

    client_max_body_size 500M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts pour les gros fichiers
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }

    location /static {
        alias /var/www/doublesub/static;
        expires 30d;
    }
}
```

Activer:
```bash
sudo ln -s /etc/nginx/sites-available/doublesub.io /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## SSL avec Let's Encrypt (Recommandé)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d doublesub.io -d www.doublesub.io
```

Certbot configurera automatiquement HTTPS!

## Nettoyage automatique

Créez un cron job pour nettoyer les vieux fichiers:

```bash
crontab -e
```

Ajouter:
```
0 2 * * * find /var/www/doublesub/uploads -type f -mtime +1 -delete
```

Cela supprime les fichiers de plus de 24h chaque jour à 2h du matin.

## Monitoring

### Voir les logs
```bash
# Logs Gunicorn
sudo journalctl -u doublesub -f

# Logs Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Redémarrer après modifications
```bash
# Après modification du code
cd /var/www/doublesub
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart doublesub

# Après modification Nginx
sudo nginx -t
sudo systemctl restart nginx
```

## Sécurité

1. **Firewall**
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. **Permissions**
```bash
sudo chown -R www-data:www-data /var/www/doublesub
sudo chmod -R 755 /var/www/doublesub
sudo chmod 775 /var/www/doublesub/uploads
```

3. **Rate Limiting** (dans Nginx)
Ajoutez dans le bloc `http` de `/etc/nginx/nginx.conf`:
```nginx
limit_req_zone $binary_remote_addr zone=upload:10m rate=5r/m;
```

Et dans votre `server` block:
```nginx
location /api/ {
    limit_req zone=upload burst=10;
    proxy_pass http://127.0.0.1:5000;
    # ... rest of proxy config
}
```

## Maintenance

### Mise à jour
```bash
cd /var/www/doublesub
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart doublesub
```

### Backup
```bash
# Sauvegarder le code (si modifié localement)
tar -czf doublesub-backup-$(date +%Y%m%d).tar.gz /var/www/doublesub

# Note: Les fichiers uploads/ sont temporaires et n'ont pas besoin de backup
```

## Troubleshooting

### Le site ne charge pas
```bash
# Vérifier le service
sudo systemctl status doublesub

# Vérifier Nginx
sudo nginx -t
sudo systemctl status nginx

# Voir les erreurs
sudo journalctl -u doublesub -n 50
```

### Erreur 413 (fichier trop gros)
Augmentez dans `/etc/nginx/sites-available/doublesub.io`:
```nginx
client_max_body_size 1000M;
```

### Timeout sur gros fichiers
Augmentez les timeouts dans la config Nginx (voir ci-dessus).

---

**Votre site est maintenant en ligne sur https://doublesub.io ! 🎉**
