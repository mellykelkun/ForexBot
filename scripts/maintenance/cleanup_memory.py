# memory_fix.py - VERSION UNIVERSELLE
import gc
import psutil
import os
import sys
from datetime import datetime

def safe_import(module_name):
    """Import sécurisé d'un module"""
    try:
        if module_name == "tensorflow":
            import tensorflow as tf
            return tf
        elif module_name == "matplotlib":
            import matplotlib.pyplot as plt
            return plt
        elif module_name == "pandas":
            import pandas as pd
            return pd
        return None
    except ImportError:
        return None
    except Exception as e:
        print(f"⚠️ Erreur import {module_name}: {e}")
        return None

def emergency_memory_cleanup():
    """Nettoyage d'urgence de la mémoire"""
    print("🚨 NETTOYAGE URGENCE MÉMOIRE")
    print("=" * 50)
    
    # Mémoire avant
    memory_before = psutil.virtual_memory()
    print(f"📊 AVANT: {memory_before.percent}% RAM")
    print(f"💾 Mémoire disponible: {memory_before.available / 1024 / 1024 / 1024:.1f} GB")
    
    # 1. Nettoyage TensorFlow si présent
    print("\n🔹 Étape 1: Nettoyage TensorFlow...")
    tf = safe_import("tensorflow")
    if tf:
        try:
            tf.keras.backend.clear_session()
            print("   ✅ TensorFlow nettoyé")
        except Exception:
            print("   ❌ Erreur nettoyage TensorFlow")
    else:
        print("   ℹ️ TensorFlow non installé")
    
    # 2. Nettoyage matplotlib si présent
    print("🔹 Étape 2: Nettoyage matplotlib...")
    plt = safe_import("matplotlib")
    if plt:
        try:
            plt.close('all')
            print("   ✅ Matplotlib nettoyé")
        except Exception:
            print("   ❌ Erreur nettoyage matplotlib")
    else:
        print("   ℹ️ Matplotlib non installé")
    
    # 3. Garbage collection agressif
    print("🔹 Étape 3: Garbage collection...")
    total_collected = 0
    for i in range(5):
        collected = gc.collect()
        total_collected += collected
        if collected > 0:
            print(f"   Pass {i+1}: {collected} objets collectés")
    
    # 4. Nettoyage caches Python
    print("🔹 Étape 4: Nettoyage caches Python...")
    try:
        # Vider le cache des types
        if hasattr(sys, '_clear_type_cache'):
            sys._clear_type_cache()
            print("   ✅ Cache types nettoyé")
        
        # Vider quelques caches spécifiques
        gc.collect()
        
    except Exception as e:
        print(f"   ⚠️ Erreur caches: {e}")
    
    # 5. Nettoyage mémoire système
    print("🔹 Étape 5: Libération mémoire système...")
    try:
        # Forcer la libération mémoire
        if hasattr(gc, 'get_referrers'):
            gc.collect()
    except Exception:
        pass
    
    # Résultats
    memory_after = psutil.virtual_memory()
    memory_freed = memory_before.percent - memory_after.percent
    memory_freed_mb = (memory_before.used - memory_after.used) / 1024 / 1024
    
    print("\n" + "=" * 50)
    print("📊 RÉSULTATS:")
    print(f"   AVANT: {memory_before.percent}% RAM")
    print(f"   APRÈS: {memory_after.percent}% RAM")
    print(f"   LIBÉRÉ: {memory_freed:.1f}% ({memory_freed_mb:.1f} MB)")
    print(f"   OBJETS: {total_collected} objets collectés")
    print("=" * 50)
    
    if memory_freed > 5:
        print("✅ SUCCÈS: Nettoyage efficace!")
    elif memory_freed > 0:
        print("⚠️  Résultat limité - Redémarrage recommandé")
    else:
        print("❌ Aucune amélioration - Voir solutions ci-dessous")
    
    return memory_freed

def analyze_memory_usage():
    """Analyse détaillée de l'utilisation mémoire"""
    print("\n🔍 ANALYSE MÉMOIRE DÉTAILLÉE")
    print("=" * 50)
    
    # Processus courant
    current_process = psutil.Process(os.getpid())
    print(f"📱 Processus courant: {current_process.memory_info().rss / 1024 / 1024:.1f} MB")
    
    # Top 10 processus gourmands
    print("\n🏆 TOP 10 PROCESSUS GOURMANDS:")
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                if memory_mb > 10:  # Plus de 10 MB
                    processes.append((proc.info['name'], memory_mb, proc.info['pid']))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Trier par mémoire utilisée
        processes.sort(key=lambda x: x[1], reverse=True)
        
        for i, (name, memory, pid) in enumerate(processes[:10]):
            print(f"   {i+1:2d}. {name[:30]:30} {memory:6.1f} MB (PID: {pid})")
            
    except Exception as e:
        print(f"   ⚠️ Impossible d'analyser: {e}")

if __name__ == "__main__":
    # Nettoyage principal
    result = emergency_memory_cleanup()
    
    # Analyse si le résultat est faible
    if result < 10:
        analyze_memory_usage()
        
        print("\n💡 SOLUTIONS RECOMMANDÉES:")
        print("   1. Redémarrez votre ordinateur")
        print("   2. Fermez les applications inutiles")
        print("   3. Vérifiez les processus en arrière-plan")
        print("   4. Augmentez la mémoire virtuelle")