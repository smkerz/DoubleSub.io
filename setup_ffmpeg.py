"""
Script pour telecharger et installer FFmpeg localement dans le projet
"""

import os
import sys
import zipfile
import urllib.request
import shutil

# URL de telechargement FFmpeg pour Windows (version essentials)
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
FFMPEG_DIR = os.path.join(os.path.dirname(__file__), 'ffmpeg')
FFMPEG_BIN_DIR = os.path.join(FFMPEG_DIR, 'bin')


def download_progress(count, block_size, total_size):
    """Affiche la progression du telechargement"""
    percent = int(count * block_size * 100 / total_size)
    percent = min(percent, 100)
    sys.stdout.write(f"\rTelechargement: {percent}%")
    sys.stdout.flush()


def download_ffmpeg():
    """Telecharge FFmpeg depuis le site officiel"""
    zip_path = os.path.join(os.path.dirname(__file__), 'ffmpeg_temp.zip')

    print("Telechargement de FFmpeg...")
    print(f"URL: {FFMPEG_URL}")
    print("Cela peut prendre quelques minutes...")
    print()

    try:
        urllib.request.urlretrieve(FFMPEG_URL, zip_path, download_progress)
        print("\n")
        return zip_path
    except Exception as e:
        print(f"\nErreur de telechargement: {e}")
        return None


def extract_ffmpeg(zip_path):
    """Extrait FFmpeg du fichier ZIP"""
    print("Extraction de FFmpeg...")

    try:
        # Creer le dossier ffmpeg
        os.makedirs(FFMPEG_DIR, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Lister les fichiers pour trouver le dossier racine
            names = zip_ref.namelist()

            # Trouver le nom du dossier racine (ex: ffmpeg-7.0-essentials_build)
            root_dir = None
            for name in names:
                if name.endswith('/bin/ffmpeg.exe'):
                    root_dir = name.split('/bin/')[0]
                    break

            if not root_dir:
                print("Erreur: Structure du ZIP non reconnue")
                return False

            # Extraire seulement le dossier bin
            bin_path = f"{root_dir}/bin/"
            for name in names:
                if name.startswith(bin_path) and not name.endswith('/'):
                    # Extraire le fichier
                    target_name = name.replace(bin_path, '')
                    target_path = os.path.join(FFMPEG_BIN_DIR, target_name)

                    os.makedirs(os.path.dirname(target_path), exist_ok=True)

                    with zip_ref.open(name) as source:
                        with open(target_path, 'wb') as target:
                            target.write(source.read())

        print(f"FFmpeg extrait dans: {FFMPEG_BIN_DIR}")
        return True

    except Exception as e:
        print(f"Erreur d'extraction: {e}")
        return False


def cleanup(zip_path):
    """Supprime le fichier ZIP temporaire"""
    try:
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print("Fichier temporaire supprime.")
    except:
        pass


def check_ffmpeg_exists():
    """Verifie si FFmpeg est deja installe localement"""
    ffmpeg_exe = os.path.join(FFMPEG_BIN_DIR, 'ffmpeg.exe')
    ffprobe_exe = os.path.join(FFMPEG_BIN_DIR, 'ffprobe.exe')
    return os.path.exists(ffmpeg_exe) and os.path.exists(ffprobe_exe)


def get_ffmpeg_paths():
    """Retourne les chemins vers ffmpeg et ffprobe"""
    return {
        'ffmpeg': os.path.join(FFMPEG_BIN_DIR, 'ffmpeg.exe'),
        'ffprobe': os.path.join(FFMPEG_BIN_DIR, 'ffprobe.exe')
    }


def main():
    """Point d'entree principal"""
    print("=" * 50)
    print("   DoubleSub.io - Installation de FFmpeg")
    print("=" * 50)
    print()

    # Verifier si deja installe
    if check_ffmpeg_exists():
        print("FFmpeg est deja installe localement!")
        paths = get_ffmpeg_paths()
        print(f"  ffmpeg:  {paths['ffmpeg']}")
        print(f"  ffprobe: {paths['ffprobe']}")
        return True

    # Telecharger
    zip_path = download_ffmpeg()
    if not zip_path:
        return False

    # Extraire
    success = extract_ffmpeg(zip_path)

    # Nettoyer
    cleanup(zip_path)

    if success:
        print()
        print("=" * 50)
        print("   FFmpeg installe avec succes!")
        print("=" * 50)
        paths = get_ffmpeg_paths()
        print(f"  ffmpeg:  {paths['ffmpeg']}")
        print(f"  ffprobe: {paths['ffprobe']}")
        print()
        print("Vous pouvez maintenant utiliser le mode video!")
        return True
    else:
        print("Echec de l'installation de FFmpeg")
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
