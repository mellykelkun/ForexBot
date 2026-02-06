#!/usr/bin/env python3
"""
Script d'installation et vérification du Micro Scalper V8 Pro
"""

import os
import sys
import subprocess

def check_environment():
    """Vérifie l'environnement et les dépendances"""
    print("🔍 Vérification de l'environnement...")
    
    # Vérifier Python
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ requis")
        return False
    
    # Vérifier .env
    if not os.path.exists('.env'):
        print("⚠️  Fichier .env non trouvé")
        print("📋 Création à partir de .env.example...")
        if os.path.exists('.env.example'):
            with open('.env.example', 'r') as f:
                template = f.read()
            with open('.env', 'w') as f:
                f.write(template)
            print("✅ .env créé - Remplissez avec vos identifiants")
        else:
            print("❌ .env.example non trouvé")
            return False
    
    print("✅ Environnement OK")
    return True

def install_dependencies():
    """Installe les dépendances"""
    print("📦 Installation des dépendances...")
    
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dépendances installées")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur installation dépendances: {e}")
        return False

def main():
    """Point d'entrée principal"""
    print("🚀 Micro Scalper V8 Pro - Setup")
    print("=" * 50)
    
    if not check_environment():
        sys.exit(1)
    
    if not install_dependencies():
        sys.exit(1)
    
    print("\n🎉 Installation terminée!")
    print("\n📋 Prochaines étapes:")
    print("1. 📝 Éditez le fichier .env avec vos identifiants MT5")
    print("2. 🔧 Vérifiez la configuration dans backend/config/config_micro_scalping_pro.py")
    print("3. 🧪 Testez en mode PAPER: python main.py --mode PAPER")
    print("4. 🚀 Lancez en production: python lanceur_automatique.py")
    
    print("\n⚡ Commandes rapides:")
    print("  python main.py --mode PAPER")
    print("  python lanceur_automatique.py")
    print("  python backend/ai/adaptive_engine.py")

if __name__ == '__main__':
    main()