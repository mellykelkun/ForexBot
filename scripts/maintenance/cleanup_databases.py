#!/usr/bin/env python3
"""
SCRIPT DE NETTOYAGE WINDOWS - FOREX BOT
"""

import os
import sqlite3
import glob
import shutil
import time
import subprocess
from datetime import datetime, timedelta

def kill_python_processes():
    """Tue tous les processus Python (Windows)"""
    try:
        # Méthode Windows
        result = subprocess.run(['taskkill', '/f', '/im', 'python.exe'], 
                              capture_output=True, text=True)
        if "SUCCESS" in result.stdout or "terminé" in result.stdout:
            print("✅ Tous les processus Python arrêtés")
        time.sleep(2)
    except Exception as e:
        print(f"⚠️ Erreur arrêt processus: {e}")

def force_cleanup_ai_training_db():
    """Nettoie la base de données en forçant la fermeture"""
    db_file = 'ai_training.db'
    
    if not os.path.exists(db_file):
        print("❌ ai_training.db non trouvée")
        return
    
    try:
        # Tenter une connexion normale d'abord
        try:
            conn = sqlite3.connect(db_file, timeout=10.0)
            cursor = conn.cursor()
            
            # Compter les données avant nettoyage
            cursor.execute("SELECT COUNT(*) FROM market_features")
            before_market = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM ai_signals") 
            before_signals = cursor.fetchone()[0]
            
            print(f"📊 Avant nettoyage - Market: {before_market}, Signals: {before_signals}")
            
            # Supprimer les données anciennes (garder seulement 2 jours)
            cutoff_date = datetime.now() - timedelta(days=2)
            
            cursor.execute("DELETE FROM market_features WHERE timestamp < ?", (cutoff_date,))
            market_deleted = cursor.rowcount
            
            cursor.execute("DELETE FROM ai_signals WHERE timestamp < ?", (cutoff_date,))
            signals_deleted = cursor.rowcount
            
            cursor.execute("DELETE FROM model_performance WHERE timestamp < ?", (cutoff_date,))
            perf_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            print(f"🧹 Données supprimées - Market: {market_deleted}, Signals: {signals_deleted}, Perf: {perf_deleted}")
            
        except sqlite3.OperationalError as e:
            print(f"⚠️ Base verrouillée: {e}")
            return
        
        # Attendre et faire VACUUM
        time.sleep(1)
        
        # VACUUM avec nouvelle connexion
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("VACUUM")
        conn.commit()
        conn.close()
        
        # Vérifier taille finale
        new_size = os.path.getsize(db_file) / (1024 * 1024)
        print(f"✅ Base optimisée - Taille: {new_size:.2f} MB")
        
    except Exception as e:
        print(f"❌ Erreur nettoyage base: {e}")

def cleanup_log_files():
    """Nettoie les fichiers logs volumineux"""
    log_files = glob.glob("*.log") + glob.glob("logs/*.log") if os.path.exists("logs") else []
    
    total_freed = 0
    for log_file in log_files:
        try:
            size_mb = os.path.getsize(log_file) / (1024 * 1024)
            if size_mb > 5:  # Supprimer logs > 5MB
                os.remove(log_file)
                print(f"🧹 Log supprimé: {log_file} ({size_mb:.1f} MB)")
                total_freed += size_mb
        except Exception as e:
            print(f"⚠️ Impossible de supprimer {log_file}: {e}")
    
    if total_freed > 0:
        print(f"💾 Espace libéré: {total_freed:.1f} MB")

def cleanup_temp_files():
    """Nettoie les fichiers temporaires"""
    temp_files = glob.glob("*.tmp") + glob.glob("*.cache") + glob.glob("temp_*")
    
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
            print(f"🧹 Fichier temporaire: {temp_file}")
        except:
            pass

def check_system_health():
    """Vérifie la santé du système"""
    print("\n📊 SANTÉ SYSTÈME:")
    
    # Taille bases de données
    db_files = ['ai_training.db', 'evolutionary_brain_model.h5']
    for db_file in db_files:
        if os.path.exists(db_file):
            size_mb = os.path.getsize(db_file) / (1024 * 1024)
            print(f"   {db_file}: {size_mb:.2f} MB")
    
    # Espace disque
    try:
        disk_usage = shutil.disk_usage(".")
        free_gb = disk_usage.free / (1024**3)
        print(f"   💾 Espace disque libre: {free_gb:.1f} GB")
    except:
        pass

def recreate_database_if_corrupted():
    """Recrée la base si corrompue"""
    db_file = 'ai_training.db'
    
    if os.path.exists(db_file):
        try:
            # Tester si la base est accessible
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            print("✅ Base de données saine")
        except sqlite3.DatabaseError:
            print("🔄 Base corrompue - recréation...")
            os.rename(db_file, f"{db_file}.corrupted")
            print("✅ Nouvelle base créée")

if __name__ == "__main__":
    print("=" * 50)
    print("🧹 NETTOYAGE WINDOWS - FOREX BOT")
    print("=" * 50)
    
    # Vérifier santé avant
    check_system_health()
    
    # Arrêter les processus Python
    print("\n🛑 ARRÊT DES PROCESSUS PYTHON...")
    kill_python_processes()
    
    # Nettoyage
    print("\n🧹 NETTOYAGE EN COURS...")
    cleanup_temp_files()
    cleanup_log_files()
    recreate_database_if_corrupted()
    force_cleanup_ai_training_db()
    
    # Vérifier santé après
    print("\n📊 SANTÉ APRÈS NETTOYAGE:")
    check_system_health()
    
    print("\n" + "=" * 50)
    print("✅ NETTOYAGE TERMINÉ!")
    print("🚀 Redémarrez: python lanceur_automatique.py")
    print("=" * 50)
