# restart_bot.py
import os
import subprocess
import sys
import time

import psutil

print("🔄 REDÉMARRAGE AUTOMATIQUE DU BOT...")
print("Fermeture des processus ForexBot...")

# Tuer UNIQUEMENT les processus ForexBot (pas tous les Python)
current_pid = os.getpid()
for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        if proc.info['pid'] == current_pid:
            continue
        cmdline = proc.info.get('cmdline') or []
        cmdline_str = ' '.join(cmdline).lower()
        if 'lanceur_automatique' in cmdline_str or 'bot_btcusd' in cmdline_str:
            print(f"  → Arrêt PID {proc.info['pid']}: {cmdline_str[:80]}")
            proc.terminate()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

time.sleep(2)

print("Nettoyage mémoire...")
# Nettoyage mémoire
import gc
gc.collect()

print("Redémarrage du bot...")
# Redémarrer le bot
subprocess.Popen(["python", "lanceur_automatique.py"])
print("✅ Bot redémarré!")