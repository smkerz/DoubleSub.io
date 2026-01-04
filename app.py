"""
DoubleSub.io - Application Flask principale
"""

import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, Response
from werkzeug.utils import secure_filename
from functools import wraps
from config import Config

# Activity log file
ACTIVITY_LOG_FILE = os.path.join(os.path.dirname(__file__), 'activity_log.json')


def log_activity(action, details=None, ip=None):
    """Log une activite utilisateur"""
    try:
        logs = []
        if os.path.exists(ACTIVITY_LOG_FILE):
            with open(ACTIVITY_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)

        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': action,
            'details': details or {},
            'ip': ip or 'unknown'
        }

        logs.insert(0, log_entry)  # Plus recent en premier
        logs = logs[:500]  # Garder les 500 derniers

        with open(ACTIVITY_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erreur log: {e}")


def get_activity_logs(limit=100):
    """Recupere les logs d'activite"""
    if os.path.exists(ACTIVITY_LOG_FILE):
        with open(ACTIVITY_LOG_FILE, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        return logs[:limit]
    return []

# Admin credentials (default, will be overridden by file if exists)
DEFAULT_ADMIN_USERNAME = 'apps@mcdavidian'
DEFAULT_ADMIN_PASSWORD = 'TheManny'
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'admin_credentials.json')


def get_admin_credentials():
    """Recupere les credentials admin depuis le fichier ou les valeurs par defaut"""
    if os.path.exists(CREDENTIALS_FILE):
        try:
            with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                creds = json.load(f)
                return creds.get('username', DEFAULT_ADMIN_USERNAME), creds.get('password', DEFAULT_ADMIN_PASSWORD)
        except:
            pass
    return DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD


def save_admin_credentials(username, password):
    """Sauvegarde les nouveaux credentials admin"""
    with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'username': username, 'password': password}, f)


from utils.subtitle_merger import SubtitleMerger
from utils.ffmpeg_helper import FFmpegHelper

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Initialiser les helpers
ffmpeg_helper = FFmpegHelper(app.config['FFMPEG_PATH'], app.config['FFPROBE_PATH'])
subtitle_merger = SubtitleMerger()


@app.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')


@app.route('/api/extract-subtitles', methods=['POST'])
def extract_subtitles():
    """Extrait les sous-titres d'une vidéo uploadée"""
    try:
        if 'video' not in request.files:
            return jsonify({'success': False, 'error': 'Aucune vidéo fournie'}), 400

        video_file = request.files['video']
        if video_file.filename == '':
            return jsonify({'success': False, 'error': 'Nom de fichier vide'}), 400

        # Sauvegarder temporairement
        filename = secure_filename(video_file.filename)
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        video_file.save(video_path)

        # Extraire les infos sur les sous-titres
        subtitles = ffmpeg_helper.get_subtitle_streams(video_path)

        if not subtitles:
            return jsonify({
                'success': True,
                'subtitles': [],
                'message': 'Aucun sous-titre trouvé dans cette vidéo'
            })

        return jsonify({
            'success': True,
            'subtitles': subtitles,
            'video_path': filename
        })

    except Exception as e:
        app.logger.error(f"Erreur extraction: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/merge', methods=['POST'])
def merge_subtitles():
    """Fusionne les sous-titres"""
    try:
        mode = request.form.get('mode', 'all')
        tolerance = int(request.form.get('tolerance', 700))

        # Mode vidéo ou mode SRT
        if 'video' in request.files:
            # Mode vidéo: extraire et fusionner
            video_file = request.files['video']
            primary_index = int(request.form.get('primary_index'))
            secondary_index = int(request.form.get('secondary_index'))

            # Sauvegarder vidéo
            filename = secure_filename(video_file.filename)
            video_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            video_file.save(video_path)

            # Extraire les sous-titres
            srt1_path = ffmpeg_helper.extract_subtitle(video_path, primary_index)
            srt2_path = ffmpeg_helper.extract_subtitle(video_path, secondary_index)

            if not srt1_path or not srt2_path:
                return jsonify({
                    'success': False,
                    'error': 'Impossible d\'extraire les sous-titres'
                }), 500

        else:
            # Mode SRT direct
            if 'srt1' not in request.files or 'srt2' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'Deux fichiers SRT sont requis'
                }), 400

            srt1_file = request.files['srt1']
            srt2_file = request.files['srt2']

            # Sauvegarder les SRT
            srt1_filename = secure_filename(srt1_file.filename)
            srt2_filename = secure_filename(srt2_file.filename)

            srt1_path = os.path.join(app.config['UPLOAD_FOLDER'], srt1_filename)
            srt2_path = os.path.join(app.config['UPLOAD_FOLDER'], srt2_filename)

            srt1_file.save(srt1_path)
            srt2_file.save(srt2_path)

        # Fusionner
        output_filename = 'merged_' + str(hash(os.urandom(16))) + '.srt'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        result = subtitle_merger.merge(
            srt1_path,
            srt2_path,
            output_path,
            mode=mode,
            tolerance_ms=tolerance
        )

        if result['success']:
            # Log l'activite
            log_activity('merge', {
                'cue_count': result['cue_count'],
                'mode': mode
            }, request.remote_addr)

            return jsonify({
                'success': True,
                'message': 'Fusion réussie!',
                'output_file': output_filename,
                'cue_count': result['cue_count']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Erreur inconnue')
            }), 500

    except Exception as e:
        app.logger.error(f"Erreur fusion: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Télécharge le fichier fusionné"""
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))

        if not os.path.exists(filepath):
            return jsonify({'error': 'Fichier introuvable'}), 404

        return send_file(
            filepath,
            as_attachment=True,
            download_name='doublesub_merged.srt',
            mimetype='text/plain'
        )

    except Exception as e:
        app.logger.error(f"Erreur téléchargement: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'service': 'doublesub.io'})


@app.route('/api/notify', methods=['POST'])
def notify_signup():
    """Enregistre un email pour notification de la fonctionnalite video"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()

        if not email or '@' not in email:
            return jsonify({'success': False, 'error': 'Email invalide'}), 400

        # Sauvegarder dans un fichier simple
        emails_file = os.path.join(os.path.dirname(__file__), 'emails_notify.txt')

        with open(emails_file, 'a', encoding='utf-8') as f:
            f.write(email + '\n')

        # Log l'activite
        log_activity('email_signup', {'email': email}, request.remote_addr)

        app.logger.info(f"Nouvel email enregistre: {email}")

        return jsonify({'success': True, 'message': 'Email enregistre'})

    except Exception as e:
        app.logger.error(f"Erreur notification: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== ADMIN BACKOFFICE ====================

def get_emails():
    """Recupere la liste des emails"""
    emails_file = os.path.join(os.path.dirname(__file__), 'emails_notify.txt')
    if os.path.exists(emails_file):
        with open(emails_file, 'r', encoding='utf-8') as f:
            emails = [line.strip() for line in f.readlines() if line.strip()]
        return emails
    return []


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Page admin avec login"""
    error = None
    success_msg = None

    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')

        admin_user, admin_pass = get_admin_credentials()

        if username == admin_user and password == admin_pass:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = 'Identifiants incorrects'

    logged_in = session.get('admin_logged_in', False)
    emails = get_emails() if logged_in else []
    current_username, _ = get_admin_credentials() if logged_in else ('', '')

    return render_template('admin.html',
                         logged_in=logged_in,
                         emails=emails,
                         email_count=len(emails),
                         error=error,
                         success_msg=success_msg,
                         current_username=current_username)


@app.route('/admin/logout')
def admin_logout():
    """Deconnexion admin"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin'))


@app.route('/admin/export')
def admin_export():
    """Export CSV des emails"""
    if not session.get('admin_logged_in', False):
        return redirect(url_for('admin'))

    emails = get_emails()
    csv_content = "email\n" + "\n".join(emails)

    return Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=doublesub_emails.csv'}
    )


@app.route('/admin/activity')
def admin_activity():
    """Page historique des activites"""
    if not session.get('admin_logged_in', False):
        return redirect(url_for('admin'))

    logs = get_activity_logs(100)
    return render_template('admin_activity.html', logs=logs)


@app.route('/admin/settings', methods=['GET', 'POST'])
def admin_settings():
    """Page de parametres admin"""
    if not session.get('admin_logged_in', False):
        return redirect(url_for('admin'))

    error = None
    success_msg = None
    current_username, _ = get_admin_credentials()

    if request.method == 'POST':
        new_username = request.form.get('new_username', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        current_password = request.form.get('current_password', '')

        # Verifier le mot de passe actuel
        _, admin_pass = get_admin_credentials()
        if current_password != admin_pass:
            error = 'Mot de passe actuel incorrect'
        elif new_password and new_password != confirm_password:
            error = 'Les nouveaux mots de passe ne correspondent pas'
        elif not new_username:
            error = 'Le nom d\'utilisateur ne peut pas etre vide'
        else:
            # Sauvegarder les nouveaux credentials
            final_password = new_password if new_password else admin_pass
            save_admin_credentials(new_username, final_password)
            current_username = new_username
            success_msg = 'Identifiants mis a jour avec succes!'

    return render_template('admin_settings.html',
                         current_username=current_username,
                         error=error,
                         success_msg=success_msg)


if __name__ == '__main__':
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
