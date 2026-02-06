# restart_bot.py
import os
import subprocess
import time

print("🔄 REDÉMARRAGE AUTOMATIQUE DU BOT...")
print("Fermeture des processus...")

# Tuer les processus Python existants
os.system("taskkill /f /im python.exe 2>nul")
time.sleep(2)

print("Nettoyage mémoire...")
# Nettoyage mémoire
import gc
gc.collect()

print("Redémarrage du bot...")
# Redémarrer le bot
subprocess.Popen(["python", "lanceur_automatique.py"])
print("✅ Bot redémarré!")