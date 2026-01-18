"""
Gestion des cles API anonymes pour DoubleSub.io
"""

import os
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

# Fichier de stockage des cles API
API_KEYS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'api_keys.json')

# Configuration du rate limiting
DAILY_LIMIT = 50  # Nombre max de fusions par jour
RATE_LIMIT_WINDOW = 24 * 60 * 60  # 24 heures en secondes


def generate_api_key():
    """Genere une nouvelle cle API unique"""
    return 'dsub_' + secrets.token_hex(16)


def hash_key(api_key):
    """Hash une cle API pour le stockage (securite)"""
    return hashlib.sha256(api_key.encode()).hexdigest()


def load_api_keys():
    """Charge les cles API depuis le fichier JSON"""
    if os.path.exists(API_KEYS_FILE):
        try:
            with open(API_KEYS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {'keys': {}, 'ip_keys': {}}


def save_api_keys(data):
    """Sauvegarde les cles API dans le fichier JSON"""
    with open(API_KEYS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_api_key(ip_address=None):
    """
    Cree une nouvelle cle API anonyme.

    Returns:
        dict: {'api_key': 'dsub_xxx...', 'created': '...', 'daily_limit': 50}
    """
    data = load_api_keys()

    # Verifier si cette IP a deja une cle
    if ip_address and ip_address in data.get('ip_keys', {}):
        existing_key_hash = data['ip_keys'][ip_address]
        if existing_key_hash in data['keys']:
            key_data = data['keys'][existing_key_hash]
            # On ne peut pas retourner la cle originale (hashee), on en genere une nouvelle
            # mais on garde les stats

    # Generer nouvelle cle
    api_key = generate_api_key()
    key_hash = hash_key(api_key)

    now = datetime.now().isoformat()

    key_data = {
        'created': now,
        'ip': ip_address or 'unknown',
        'usage': [],
        'total_merges': 0,
        'last_used': None,
        'active': True
    }

    data['keys'][key_hash] = key_data

    # Associer IP a cette cle
    if ip_address:
        data['ip_keys'][ip_address] = key_hash

    save_api_keys(data)

    return {
        'api_key': api_key,
        'created': now,
        'daily_limit': DAILY_LIMIT
    }


def validate_api_key(api_key):
    """
    Valide une cle API et verifie les limites.

    Returns:
        dict: {'valid': bool, 'error': str or None, 'remaining': int}
    """
    if not api_key or not api_key.startswith('dsub_'):
        return {'valid': False, 'error': 'Invalid API key format', 'remaining': 0}

    data = load_api_keys()
    key_hash = hash_key(api_key)

    if key_hash not in data['keys']:
        return {'valid': False, 'error': 'API key not found', 'remaining': 0}

    key_data = data['keys'][key_hash]

    if not key_data.get('active', True):
        return {'valid': False, 'error': 'API key is disabled', 'remaining': 0}

    # Compter les utilisations des dernieres 24h
    now = datetime.now()
    cutoff = now - timedelta(hours=24)

    recent_usage = [
        u for u in key_data.get('usage', [])
        if datetime.fromisoformat(u) > cutoff
    ]

    used_today = len(recent_usage)
    remaining = max(0, DAILY_LIMIT - used_today)

    if remaining <= 0:
        return {
            'valid': False,
            'error': f'Daily limit exceeded ({DAILY_LIMIT} merges/day). Resets in 24h.',
            'remaining': 0
        }

    return {'valid': True, 'error': None, 'remaining': remaining}


def record_usage(api_key):
    """Enregistre une utilisation de la cle API"""
    if not api_key:
        return

    data = load_api_keys()
    key_hash = hash_key(api_key)

    if key_hash not in data['keys']:
        return

    now = datetime.now()

    # Ajouter l'usage
    data['keys'][key_hash]['usage'].append(now.isoformat())
    data['keys'][key_hash]['total_merges'] = data['keys'][key_hash].get('total_merges', 0) + 1
    data['keys'][key_hash]['last_used'] = now.isoformat()

    # Nettoyer les vieux usages (garder seulement 48h)
    cutoff = now - timedelta(hours=48)
    data['keys'][key_hash]['usage'] = [
        u for u in data['keys'][key_hash]['usage']
        if datetime.fromisoformat(u) > cutoff
    ]

    save_api_keys(data)


def get_key_stats(api_key):
    """Recupere les statistiques d'une cle API"""
    if not api_key:
        return None

    data = load_api_keys()
    key_hash = hash_key(api_key)

    if key_hash not in data['keys']:
        return None

    key_data = data['keys'][key_hash]

    # Compter les utilisations des dernieres 24h
    now = datetime.now()
    cutoff = now - timedelta(hours=24)

    recent_usage = [
        u for u in key_data.get('usage', [])
        if datetime.fromisoformat(u) > cutoff
    ]

    return {
        'created': key_data.get('created'),
        'total_merges': key_data.get('total_merges', 0),
        'used_today': len(recent_usage),
        'remaining_today': max(0, DAILY_LIMIT - len(recent_usage)),
        'daily_limit': DAILY_LIMIT,
        'last_used': key_data.get('last_used'),
        'active': key_data.get('active', True)
    }


def get_all_keys_stats():
    """Recupere les stats de toutes les cles (pour admin)"""
    data = load_api_keys()
    stats = []

    now = datetime.now()
    cutoff = now - timedelta(hours=24)

    for key_hash, key_data in data.get('keys', {}).items():
        recent_usage = [
            u for u in key_data.get('usage', [])
            if datetime.fromisoformat(u) > cutoff
        ]

        stats.append({
            'key_hash': key_hash[:12] + '...',  # Tronque pour la securite
            'created': key_data.get('created'),
            'ip': key_data.get('ip', 'unknown'),
            'total_merges': key_data.get('total_merges', 0),
            'used_today': len(recent_usage),
            'last_used': key_data.get('last_used'),
            'active': key_data.get('active', True)
        })

    # Trier par derniere utilisation
    stats.sort(key=lambda x: x.get('last_used') or '', reverse=True)

    return stats


def toggle_key_status(key_hash_prefix):
    """Active/desactive une cle API (pour admin)"""
    data = load_api_keys()

    for key_hash in data.get('keys', {}):
        if key_hash.startswith(key_hash_prefix):
            data['keys'][key_hash]['active'] = not data['keys'][key_hash].get('active', True)
            save_api_keys(data)
            return True

    return False


def require_api_key(f):
    """Decorateur pour proteger un endpoint avec une cle API"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Chercher la cle dans les headers ou les parametres
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key') or request.form.get('api_key')

        if not api_key:
            return jsonify({
                'success': False,
                'error': 'API key required. Get one at /api/v1/key'
            }), 401

        validation = validate_api_key(api_key)

        if not validation['valid']:
            return jsonify({
                'success': False,
                'error': validation['error'],
                'remaining': validation['remaining']
            }), 403 if 'limit' in validation['error'].lower() else 401

        # Stocker la cle pour l'utiliser plus tard
        request.api_key = api_key
        request.api_remaining = validation['remaining']

        return f(*args, **kwargs)

    return decorated_function
