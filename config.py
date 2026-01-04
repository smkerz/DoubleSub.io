import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()


def get_ffmpeg_path():
    """Detecte le chemin FFmpeg (local ou systeme)"""
    # 1. Variable d'environnement
    env_path = os.environ.get('FFMPEG_PATH')
    if env_path and os.path.exists(env_path):
        return env_path

    # 2. FFmpeg local dans le projet
    base_dir = os.path.dirname(__file__)
    local_ffmpeg = os.path.join(base_dir, 'ffmpeg', 'bin', 'ffmpeg.exe')
    if os.path.exists(local_ffmpeg):
        return local_ffmpeg

    # 3. Defaut (systeme PATH)
    return 'ffmpeg'


def get_ffprobe_path():
    """Detecte le chemin FFprobe (local ou systeme)"""
    # 1. Variable d'environnement
    env_path = os.environ.get('FFPROBE_PATH')
    if env_path and os.path.exists(env_path):
        return env_path

    # 2. FFprobe local dans le projet
    base_dir = os.path.dirname(__file__)
    local_ffprobe = os.path.join(base_dir, 'ffmpeg', 'bin', 'ffprobe.exe')
    if os.path.exists(local_ffprobe):
        return local_ffprobe

    # 3. Defaut (systeme PATH)
    return 'ffprobe'


class Config:
    """Configuration pour DoubleSub.io"""

    # Securite
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024 * 1024  # 5 GB max
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv', 'webm'}
    ALLOWED_SUBTITLE_EXTENSIONS = {'srt', 'ass', 'ssa'}

    # Serveur
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # FFmpeg - detection automatique
    FFMPEG_PATH = get_ffmpeg_path()
    FFPROBE_PATH = get_ffprobe_path()

    # Nettoyage automatique
    AUTO_CLEANUP_HOURS = 24  # Supprimer les fichiers apres 24h

    @staticmethod
    def init_app(app):
        """Initialise les dossiers necessaires"""
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
