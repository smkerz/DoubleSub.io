"""
Helper pour FFmpeg - extraction de sous-titres depuis vidéos
"""

import subprocess
import json
import os
import tempfile


class FFmpegHelper:
    """Wrapper pour FFmpeg/FFprobe"""

    def __init__(self, ffmpeg_path='ffmpeg', ffprobe_path='ffprobe'):
        self.ffmpeg = ffmpeg_path
        self.ffprobe = ffprobe_path

    def get_subtitle_streams(self, video_path):
        """
        Récupère la liste des flux de sous-titres

        Returns:
            Liste de dicts: [{'index': 2, 'codec': 'srt', 'language': 'eng'}, ...]
        """
        try:
            cmd = [
                self.ffprobe,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 's',  # Seulement les sous-titres
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            subtitles = []
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'subtitle':
                    sub_info = {
                        'index': stream.get('index'),
                        'codec': stream.get('codec_name', 'unknown'),
                        'language': stream.get('tags', {}).get('language', 'und'),
                        'title': stream.get('tags', {}).get('title', '')
                    }
                    subtitles.append(sub_info)

            return subtitles

        except subprocess.CalledProcessError as e:
            print(f"FFprobe error: {e.stderr}")
            return []
        except Exception as e:
            print(f"Error: {str(e)}")
            return []

    def extract_subtitle(self, video_path, stream_index, output_dir=None):
        """
        Extrait un flux de sous-titres en SRT

        Args:
            video_path: Chemin de la vidéo
            stream_index: Index du flux de sous-titres
            output_dir: Dossier de sortie (optionnel)

        Returns:
            Chemin du fichier SRT extrait, ou None si échec
        """
        try:
            if output_dir is None:
                output_dir = tempfile.gettempdir()

            # Nom de fichier basé sur la vidéo et l'index
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}_sub{stream_index}.srt")

            cmd = [
                self.ffmpeg,
                '-y',  # Overwrite
                '-i', video_path,
                '-map', f'0:{stream_index}',  # Sélectionner le flux
                '-c:s', 'srt',  # Convertir en SRT
                output_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return output_path
            else:
                print(f"Output file empty or missing: {output_path}")
                return None

        except subprocess.CalledProcessError as e:
            print(f"FFmpeg error: {e.stderr}")
            return None
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def check_available(self):
        """Vérifie que FFmpeg et FFprobe sont disponibles"""
        try:
            subprocess.run([self.ffmpeg, '-version'], capture_output=True, check=True)
            subprocess.run([self.ffprobe, '-version'], capture_output=True, check=True)
            return True
        except:
            return False
