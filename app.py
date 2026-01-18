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
from utils.api_keys import (
    create_api_key, validate_api_key, record_usage, get_key_stats,
    get_all_keys_stats, toggle_key_status, require_api_key
)

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
        offset1 = int(request.form.get('offset1', 0))
        offset2 = int(request.form.get('offset2', 0))
        color1 = request.form.get('color1', '') or None
        color2 = request.form.get('color2', '') or None

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
            tolerance_ms=tolerance,
            offset1_ms=offset1,
            offset2_ms=offset2,
            color1=color1,
            color2=color2
        )

        if result['success']:
            # Recuperer les noms de fichiers originaux
            if 'video' in request.files:
                file1_name = secure_filename(request.files['video'].filename)
                file2_name = file1_name
            else:
                file1_name = secure_filename(request.files['srt1'].filename)
                file2_name = secure_filename(request.files['srt2'].filename)

            # Log l'activite avec les noms de fichiers
            log_activity('merge', {
                'cue_count': result['cue_count'],
                'mode': mode,
                'file1': file1_name,
                'file2': file2_name,
                'output_file': output_filename
            }, request.remote_addr)

            return jsonify({
                'success': True,
                'message': 'Fusion réussie!',
                'output_file': output_filename,
                'cue_count': result['cue_count'],
                'preview': result.get('preview', [])
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


# ==================== PUBLIC API v1 ====================

@app.route('/api/v1/merge', methods=['POST'])
@require_api_key
def api_v1_merge():
    """
    Public API endpoint for merging subtitles.

    Request (multipart/form-data):
        - srt1: First SRT file (required)
        - srt2: Second SRT file (required)
        - api_key: API key (required, or use X-API-Key header)
        - mode: Merge mode - 'all', 'overlapping', or 'primary' (optional, default: 'all')
        - tolerance: Timing tolerance in ms (optional, default: 700)
        - offset1: Time offset for first subtitle in ms (optional, default: 0)
        - offset2: Time offset for second subtitle in ms (optional, default: 0)
        - color1: HTML color for first subtitle, e.g. '#FFFFFF' (optional)
        - color2: HTML color for second subtitle, e.g. '#FFFF00' (optional)
        - format: Response format - 'file' or 'json' (optional, default: 'file')

    Response:
        - If format='file': Returns the merged SRT file directly
        - If format='json': Returns JSON with download URL and metadata

    Example curl:
        curl -X POST https://doublesub.io/api/v1/merge \\
            -H "X-API-Key: dsub_your_key_here" \\
            -F "srt1=@english.srt" \\
            -F "srt2=@french.srt" \\
            -F "mode=all" \\
            --output merged.srt
    """
    try:
        # Validate required files
        if 'srt1' not in request.files or 'srt2' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Two SRT files required (srt1 and srt2)'
            }), 400

        srt1_file = request.files['srt1']
        srt2_file = request.files['srt2']

        if srt1_file.filename == '' or srt2_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Empty filename'
            }), 400

        # Get parameters
        mode = request.form.get('mode', 'all')
        if mode not in ['all', 'overlapping', 'primary']:
            return jsonify({
                'success': False,
                'error': 'Invalid mode. Use: all, overlapping, or primary'
            }), 400

        try:
            tolerance = int(request.form.get('tolerance', 700))
            offset1 = int(request.form.get('offset1', 0))
            offset2 = int(request.form.get('offset2', 0))
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid numeric parameter'
            }), 400

        color1 = request.form.get('color1', '') or None
        color2 = request.form.get('color2', '') or None
        response_format = request.form.get('format', 'file')

        # Save uploaded files
        srt1_filename = secure_filename(srt1_file.filename)
        srt2_filename = secure_filename(srt2_file.filename)

        srt1_path = os.path.join(app.config['UPLOAD_FOLDER'], 'api_' + srt1_filename)
        srt2_path = os.path.join(app.config['UPLOAD_FOLDER'], 'api_' + srt2_filename)

        srt1_file.save(srt1_path)
        srt2_file.save(srt2_path)

        # Merge
        output_filename = 'api_merged_' + str(hash(os.urandom(16))) + '.srt'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        result = subtitle_merger.merge(
            srt1_path,
            srt2_path,
            output_path,
            mode=mode,
            tolerance_ms=tolerance,
            offset1_ms=offset1,
            offset2_ms=offset2,
            color1=color1,
            color2=color2
        )

        if not result['success']:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Merge failed')
            }), 500

        # Record API key usage (rate limiting)
        record_usage(request.api_key)

        # Log API usage
        log_activity('api_merge', {
            'cue_count': result['cue_count'],
            'mode': mode,
            'file1': srt1_filename,
            'file2': srt2_filename,
            'remaining_quota': request.api_remaining - 1
        }, request.remote_addr)

        # Return based on format
        if response_format == 'json':
            return jsonify({
                'success': True,
                'cue_count': result['cue_count'],
                'download_url': f'/download/{output_filename}',
                'preview': result.get('preview', [])[:5]  # First 5 subtitles
            })
        else:
            # Return file directly
            return send_file(
                output_path,
                as_attachment=True,
                download_name='doublesub_merged.srt',
                mimetype='text/plain'
            )

    except Exception as e:
        app.logger.error(f"API merge error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/docs')
def api_v1_docs():
    """API documentation page"""
    return render_template('api_docs.html')


# ==================== API KEY MANAGEMENT ====================

@app.route('/api/v1/key', methods=['POST'])
def api_create_key():
    """
    Cree une nouvelle cle API anonyme.

    Response:
        {
            "success": true,
            "api_key": "dsub_xxxxxxxxxxxx",
            "daily_limit": 50,
            "message": "Store this key - it cannot be recovered!"
        }
    """
    try:
        ip_address = request.remote_addr

        result = create_api_key(ip_address)

        log_activity('api_key_created', {
            'ip': ip_address
        }, ip_address)

        return jsonify({
            'success': True,
            'api_key': result['api_key'],
            'daily_limit': result['daily_limit'],
            'message': 'Store this key safely - it cannot be recovered if lost!'
        })

    except Exception as e:
        app.logger.error(f"Error creating API key: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/v1/key/validate', methods=['POST'])
def api_validate_key():
    """
    Valide une cle API et retourne son statut.

    Request:
        Header: X-API-Key: dsub_xxx
        OR Body: {"api_key": "dsub_xxx"}

    Response:
        {
            "valid": true,
            "remaining": 45,
            "daily_limit": 50
        }
    """
    try:
        api_key = request.headers.get('X-API-Key') or request.json.get('api_key') if request.is_json else None

        if not api_key:
            return jsonify({
                'valid': False,
                'error': 'API key required'
            }), 400

        validation = validate_api_key(api_key)

        return jsonify({
            'valid': validation['valid'],
            'remaining': validation['remaining'],
            'daily_limit': 50,
            'error': validation.get('error')
        })

    except Exception as e:
        app.logger.error(f"Error validating API key: {str(e)}")
        return jsonify({'valid': False, 'error': str(e)}), 500


@app.route('/api/v1/key/stats', methods=['GET'])
def api_key_stats():
    """
    Retourne les statistiques d'utilisation d'une cle API.

    Request:
        Header: X-API-Key: dsub_xxx

    Response:
        {
            "success": true,
            "stats": {
                "total_merges": 123,
                "used_today": 5,
                "remaining_today": 45,
                "daily_limit": 50,
                "created": "2024-01-15T10:30:00",
                "last_used": "2024-01-15T14:22:00"
            }
        }
    """
    try:
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')

        if not api_key:
            return jsonify({
                'success': False,
                'error': 'API key required'
            }), 400

        stats = get_key_stats(api_key)

        if not stats:
            return jsonify({
                'success': False,
                'error': 'API key not found'
            }), 404

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        app.logger.error(f"Error getting key stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


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


@app.route('/admin/download/<filename>')
def admin_download(filename):
    """Telecharge un fichier depuis l'admin"""
    if not session.get('admin_logged_in', False):
        return redirect(url_for('admin'))

    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))

        if not os.path.exists(filepath):
            return "Fichier introuvable", 404

        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype='text/plain'
        )
    except Exception as e:
        return f"Erreur: {str(e)}", 500


@app.route('/admin/view/<filename>')
def admin_view(filename):
    """Affiche le contenu d'un fichier SRT"""
    if not session.get('admin_logged_in', False):
        return redirect(url_for('admin'))

    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(filename))

        if not os.path.exists(filepath):
            return "Fichier introuvable", 404

        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        return render_template('admin_view_file.html', filename=filename, content=content)
    except Exception as e:
        return f"Erreur: {str(e)}", 500


@app.route('/admin/api-keys')
def admin_api_keys():
    """Page de gestion des cles API"""
    if not session.get('admin_logged_in', False):
        return redirect(url_for('admin'))

    keys_stats = get_all_keys_stats()
    total_keys = len(keys_stats)
    active_keys = sum(1 for k in keys_stats if k.get('active', True))
    total_merges = sum(k.get('total_merges', 0) for k in keys_stats)

    return render_template('admin_api_keys.html',
                         keys=keys_stats,
                         total_keys=total_keys,
                         active_keys=active_keys,
                         total_merges=total_merges)


@app.route('/admin/api-keys/toggle/<key_hash_prefix>', methods=['POST'])
def admin_toggle_key(key_hash_prefix):
    """Active/desactive une cle API"""
    if not session.get('admin_logged_in', False):
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    success = toggle_key_status(key_hash_prefix)

    if success:
        log_activity('api_key_toggled', {'key_prefix': key_hash_prefix}, request.remote_addr)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Key not found'}), 404


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
