"""
WSGI entry point pour le déploiement en production
"""

from app import app

if __name__ == "__main__":
    app.run()
