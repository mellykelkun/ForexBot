"""
Utilitaire de génération de clé d'accès ForexBot SaaS.

Usage :
    python generate_access_key.py

Génère une clé crypto-sécurisée 64 caractères, la hashe en SHA-256,
et stocke le hash dans le fichier .env.
"""

import os
import sys

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.security.auth import setup_access_key_interactive


if __name__ == "__main__":
    print("=" * 60)
    print("  ForexBot SaaS — Génération de clé d'accès")
    print("=" * 60)
    print()
    setup_access_key_interactive()
    print()
    print("=" * 60)
    print("  Configuration terminée.")
    print("  Lancez le bot avec : python lanceur_automatique.py")
    print("=" * 60)
