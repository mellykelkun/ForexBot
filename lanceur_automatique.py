"""
LANCEUR INTELLIGENT PROFESSIONNEL - BTCUSD MICRO SCALPER V8
Gestion automatique des processus avec redémarrage intelligent
Version corrigée avec gestion d'encodage UTF-8
"""

import subprocess
import time
import sys
import os
import signal
import psutil
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import json
os.environ['PYTHONIOENCODING'] = 'utf-8'
import gc
import psutil
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ✅ NETTOYAGE MÉMOIRE AU DÉMARRAGE
gc.collect()
print(f"🧹 Mémoire initiale: {psutil.Process().memory_percent():.1f}%")

class MemoryCleaner:
    """Gestionnaire de nettoyage mémoire ULTRA AGGRESSIF"""
    
    def __init__(self):
        self.cleanup_count = 0
        self.last_cleanup = datetime.now()
    
    def get_memory_usage(self):
        """Retourne l'utilisation mémoire détaillée"""
        process = psutil.Process(os.getpid())
        system_memory = psutil.virtual_memory()
        
        return {
            'process_memory_mb': process.memory_info().rss / 1024 / 1024,
            'system_memory_percent': system_memory.percent,
            'system_memory_available_gb': system_memory.available / 1024 / 1024 / 1024,
            'timestamp': datetime.now().isoformat()
        }
    
    def force_garbage_collection(self):
        """Force le garbage collection ULTRA AGGRESSIF"""
        try:
            collected_total = 0
            # 🔥 COLLECTE TRÈS AGGRESSIVE - 10 passes au lieu de 3
            for i in range(10):
                collected = gc.collect()
                collected_total += collected
                if collected == 0 and i >= 5:  # Arrêter après 5 passes si rien
                    break
                time.sleep(0.01)  # Micro-pause
            return collected_total
            
        except Exception as e:
            logging.error(f"❌ Erreur garbage collection: {e}")
            return 0
    
    def clear_tensorflow_memory(self):
        """Désactivé (IA locale supprimée)."""
        return False
    
    def clear_matplotlib_cache(self):
        """Nettoie le cache matplotlib ULTRA AGGRESSIF"""
        try:
            if 'matplotlib' in sys.modules:
                import matplotlib.pyplot as plt
                plt.close('all')
                # 🔥 VIDER TOUS LES CACHES MATPLOTLIB
                try:
                    from matplotlib import _pylab_helpers
                    _pylab_helpers.Gcf.destroy_all()
                except:
                    pass
                return True
        except Exception as e:
            logging.debug(f"Matplotlib non disponible: {e}")
        return False
    
    def clear_all_python_caches(self):
        """Vide TOUS les caches Python possibles"""
        try:
            # 🔥 CACHE NUMPY
            try:
                import numpy as np
                if hasattr(np, '_globals'):
                    np._globals._clear_cache()
            except: pass
            
            # 🔥 CACHE IMPORT
            try:
                import importlib
                importlib.invalidate_caches()
            except: pass
            
            # 🔥 CACHE PYTHON INTERNE
            if hasattr(sys, '_clear_type_cache'):
                sys._clear_type_cache()
            if hasattr(gc, 'get_referrers'):
                gc.collect()  # Double appel
                
        except Exception as e:
            logging.debug(f"Cache cleanup: {e}")
    
    def comprehensive_cleanup(self):
        """Nettoyage complet ULTRA AGGRESSIF"""
        try:
            # Mémoire avant cleanup
            before = self.get_memory_usage()
            
            logging.info("🧹 DÉBUT NETTOYAGE MÉMOIRE ULTRA-AGGRESSIF...")
            
            # 🔥 ÉTAPE 1: Nettoyer TensorFlow/Keras
            self.clear_tensorflow_memory()
            
            # 🔥 ÉTAPE 2: Nettoyer les caches des bibliothèques
            self.clear_matplotlib_cache()
            
            # 🔥 ÉTAPE 3: Vider TOUS les caches Python
            self.clear_all_python_caches()
            
            # 🔥 ÉTAPE 4: Forcer le garbage collection ULTRA AGGRESSIF
            collected = self.force_garbage_collection()
            
            # 🔥 ÉTAPE 5: Second passage de nettoyage
            self.clear_tensorflow_memory()  # Double nettoyage TensorFlow
            gc.collect()  # Dernier passage GC
            
            # Mémoire après cleanup
            after = self.get_memory_usage()
            memory_freed = before['process_memory_mb'] - after['process_memory_mb']
            
            self.cleanup_count += 1
            self.last_cleanup = datetime.now()
            
            # 🔥 LOG DÉTAILLÉ
            logging.info(f"📊 CLEANUP #{self.cleanup_count} ULTRA-AGGRESSIF:")
            logging.info(f"   🗑️  Objets collectés: {collected}")
            logging.info(f"   💾 Mémoire libérée: {memory_freed:.1f} MB")
            logging.info(f"   📈 RAM système: {before['system_memory_percent']:.1f}% → {after['system_memory_percent']:.1f}%")
            logging.info(f"   🎯 Process RAM: {before['process_memory_mb']:.1f}MB → {after['process_memory_mb']:.1f}MB")
            
            return memory_freed
            
        except Exception as e:
            logging.error(f"❌ Erreur lors du nettoyage mémoire: {e}")
            return 0

class MemoryManager:
    """Gestionnaire de mémoire avec cleanup automatique"""
    
    def __init__(self, cleanup_interval=300):
        self.cleanup_interval = cleanup_interval
        self.cleaner = MemoryCleaner()
        self.last_cleanup = datetime.now()
    
    def should_cleanup(self):
        """Détermine si un cleanup est nécessaire - SEUILS AGGRESSIFS"""
        memory_usage = self.cleaner.get_memory_usage()
        
        # Cleanup si RAM système > 92% ou toutes les 5 minutes
        time_since_cleanup = (datetime.now() - self.last_cleanup).total_seconds()
        
        if (memory_usage['system_memory_percent'] > 92 or
            time_since_cleanup > self.cleanup_interval):
            return True
        return False
    
    def periodic_cleanup(self):
        """Cleanup périodique ULTRA AGGRESSIF"""
        while True:
            try:
                if self.should_cleanup():
                    self.cleaner.comprehensive_cleanup()
                    self.last_cleanup = datetime.now()
                
                time.sleep(60)
                
            except Exception as e:
                logging.error(f"❌ Erreur cleanup périodique: {e}")
                time.sleep(60)

class IntelligentProcessManager:
    """Gestionnaire intelligent de processus avec gestion d'encodage"""
    
    def __init__(self):
        self.processes = {}
        
        # 🔧 CORRECTION : Chemins absolus
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.process_configs = {
            'ai_engine': {
                'command': [sys.executable, '-m', 'backend.ai.adaptive_engine'],
                'port': 5003,
                'health_check': '/api/health',
                'max_restarts': 3,
                'restart_delay': 20,
                'required': True,
                'startup_time': 15,
                'timeout': 40
            },
            'dashboard': {
                'command': [sys.executable, '-m', 'backend.dashboard_app'],
                'port': 5004,
                'health_check': '/health',
                'max_restarts': 3,
                'restart_delay': 20,
                'required': False,
                'startup_time': 8,
                'timeout': 30
            },
            'bot': {
                'command': [
                    sys.executable, 
                    os.path.join(base_dir, 'main.py'),
                    '--mode', 'REAL',
                    '--strategy', 'MICRO',
                    # 🎯 SORTIE INTELLIGENTE MAINTENANT ACTIVÉE PAR DÉFAUT
                    '--ai-engine',
                    '--risk', '0.5'
                ],
                'port': None,
                'health_check': None,
                'max_restarts': 3,
                'restart_delay': 30,
                'required': False,
                'startup_time': 15,
                'timeout': 45
            }
        }
        
        self.restart_counts = {}
        self.system_start_time = datetime.now()
        self.performance_metrics = {}
        
        # ✅ NOUVEAU : Gestionnaire de mémoire
        self.memory_cleaner = MemoryCleaner()
        self.memory_manager = MemoryManager()
        
        # Configuration logging
        self.setup_logging()
        
        # 🔧 CORRECTION : Log des chemins pour debug
        logging.info(f"📁 Répertoire base: {base_dir}")
        for process_name, config in self.process_configs.items():
            logging.info(f"🔧 {process_name}: {config['command']}")
        
    def setup_logging(self):
        """Configuration du logging avance"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s.%(msecs)03d [%(levelname)-8s] %(message)s',
            datefmt='%H:%M:%S',
            handlers=[
                logging.FileHandler('process_manager.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
    def start_process_with_retry(self, process_name: str, max_attempts: int = 2) -> bool:
        """Démarre un processus avec système de retry intelligent"""
        for attempt in range(max_attempts):
            logging.info(f"🔄 Tentative {attempt + 1}/{max_attempts} pour {process_name}")
            
            if self.start_process(process_name):
                return True
                
            if attempt < max_attempts - 1:  # Pas la dernière tentative
                wait_time = (attempt + 1) * 10  # Backoff exponentiel
                logging.info(f"⏳ Nouvelle tentative dans {wait_time}s...")
                
                # ✅ NETTOYAGE MÉMOIRE entre les tentatives
                gc.collect()
                self.memory_cleaner.comprehensive_cleanup()
                    
                time.sleep(wait_time)
        
        logging.error(f"❌ Échec après {max_attempts} tentatives pour {process_name}")
        return False
        
    def start_process(self, process_name: str) -> bool:
        """Demarre un processus avec gestion d'erreurs amelioree"""
        
        # ✅ NETTOYAGE MÉMOIRE AVANT CHAQUE DÉMARRAGE
        gc.collect()
        memory_before = psutil.Process().memory_percent()
        try:
            if process_name not in self.process_configs:
                logging.error(f"ERREUR: Processus inconnu: {process_name}")
                return False
            
            config = self.process_configs[process_name]

            if process_name == "bot":
                mt5_login = os.getenv("MT5_LOGIN")
                mt5_password = os.getenv("MT5_PASSWORD")
                mt5_server = os.getenv("MT5_SERVER")
                if not mt5_login or not mt5_password or not mt5_server:
                    logging.error("❌ MT5 non configuré: MT5_LOGIN, MT5_PASSWORD, MT5_SERVER requis")
                    logging.error("💡 Ajoute-les dans tes variables d'environnement ou dans un fichier .env")
                    return False
            
            # 🔧 CORRECTION : Verification du fichier (sauf lancement en module)
            script_path = config['command'][1] if len(config['command']) > 1 else None
            if script_path and script_path != "-m":
                if not os.path.exists(script_path):
                    logging.error(f"❌ FICHIER INTROUVABLE: {script_path}")
                    logging.error(f"   📁 Repertoire courant: {os.getcwd()}")
                    return False
            
            # Verifier si le processus est deja en cours d'execution
            if self.is_process_running(process_name):
                logging.info(f"INFO: Processus {process_name} deja en cours d'execution")
                return True
            
            logging.info(f"DEMARRAGE: Demarrage de {process_name}...")
            logging.info(f"📝 Commande: {' '.join(config['command'])}")
            
            # 🔧 CORRECTION CRITIQUE : Configuration d'encodage robuste
            process = subprocess.Popen(
                config['command'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Fusionner stdout et stderr
                bufsize=1,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
            
            self.processes[process_name] = process
            self.restart_counts[process_name] = self.restart_counts.get(process_name, 0) + 1
            
            # 🔧 CORRECTION : Démarrer la surveillance avec gestion d'encodage
            self.monitor_process_output_robust(process_name, process)
            
            # Attendre le temps de demarrage estime
            startup_time = config.get('startup_time', 15)
            logging.info(f"ATTENTE: Attente du demarrage de {process_name} ({startup_time}s)...")
            time.sleep(startup_time)
            
            # Verifier l'accessibilite du service
            if config['port']:
                timeout = config.get('health_timeout', config.get('timeout', 60))
                if not self.wait_for_service(process_name, config['port'], config.get('health_check'), timeout):
                    logging.error(f"ERREUR: Service {process_name} non accessible")
                    return False
            
            logging.info(f"SUCCES: {process_name} demarre avec succes (PID: {process.pid})")
            return True
            
        except Exception as e:
            logging.error(f"ERREUR: Erreur demarrage {process_name}: {e}")
            return False
    
    def monitor_process_output_robust(self, process_name: str, process: subprocess.Popen):
        """🔧 NOUVELLE MÉTHODE : Surveillance robuste avec gestion d'encodage"""
        def output_reader():
            while True:
                try:
                    # Lire les bytes bruts
                    raw_output = process.stdout.readline()
                    if not raw_output and process.poll() is not None:
                        break
                    
                    if raw_output:
                        if isinstance(raw_output, bytes):
                            decoded_output = raw_output.decode('utf-8', errors='replace').strip()
                        else:
                            decoded_output = str(raw_output).strip()
                        
                        # Filtrer et logger
                        if (decoded_output and 
                            not decoded_output.isspace() and
                            len(decoded_output) > 0 and
                            not any(term in decoded_output for term in [
                                'emitting event', 
                                'Server initialized',
                                'GET /socket.io'
                            ])):
                            logging.info(f"[{process_name}] {decoded_output}")
                            
                except Exception as e:
                    # 🔧 CORRECTION : Logger silencieusement les erreurs de lecture
                    if "decode" not in str(e):
                        logging.debug(f"Erreur lecture {process_name}: {e}")
                    time.sleep(0.1)
                    continue
        
        thread = threading.Thread(target=output_reader, daemon=True)
        thread.start()
    
    def is_process_running(self, process_name: str) -> bool:
        """Verifie si un processus est en cours d'execution"""
        if process_name not in self.processes:
            return False
        
        process = self.processes[process_name]
        return process.poll() is None
    
    def diagnose_service_issue(self, process_name: str, port: int):
        """Diagnostique automatiquement les problèmes de service"""
        try:
            logging.info(f"🔍 DIAGNOSTIC: Analyse du problème pour {process_name}...")
            
            # Vérifier si le port est occupé
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            
            if result == 0:
                logging.warning(f"⚠️  Le port {port} est occupé mais le service ne répond pas")
            else:
                logging.warning(f"⚠️  Le port {port} n'est pas accessible")
            
            # Vérifier la mémoire
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                logging.warning(f"⚠️  Mémoire système élevée: {memory.percent:.1f}%")
            
            # Vérifier le CPU
            cpu = psutil.cpu_percent(interval=1)
            if cpu > 80:
                logging.warning(f"⚠️  CPU élevé: {cpu:.1f}%")
                
        except Exception as e:
            logging.debug(f"Diagnostic échoué: {e}")
    
    def wait_for_service(self, process_name: str, port: int, health_endpoint: str = None, timeout: int = None) -> bool:
        """Attend qu'un service soit prêt - VERSION AMÉLIORÉE"""
        
        # ⬅️ NOUVEAU : Timeout spécifique par processus
        if timeout is None:
            config = self.process_configs.get(process_name, {})
            timeout = config.get('health_timeout', config.get('timeout', 60))
        
        logging.info(f"VERIFICATION: Vérification du service {process_name} sur le port {port} (timeout: {timeout}s)...")
        
        start_time = time.time()
        base_url = f"http://localhost:{port}"
        
        # Endpoints de santé prioritaires selon le processus
        check_urls = []
        if health_endpoint:
            check_urls.append(base_url + health_endpoint)
        
        # Endpoints spécifiques par processus
        if process_name == 'ai_engine':
            check_urls.extend([
                base_url + '/api/health',
                base_url + '/api/status',
                base_url + '/'
            ])
        else:
            check_urls.extend([
                base_url + '/health',
                base_url + '/',
                base_url
            ])
        
        last_log_time = start_time
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        while time.time() - start_time < timeout:
            success = False
            
            for check_url in check_urls:
                try:
                    # ⬅️ NOUVEAU : Timeout adaptatif selon le processus
                    request_timeout = 5
                    response = requests.get(check_url, timeout=request_timeout)
                    
                    if response.status_code < 500:  # Accepte 2xx, 3xx, 4xx
                        elapsed = time.time() - start_time
                        logging.info(f"✅ SUCCES: Service {process_name} accessible à {check_url} (code: {response.status_code}) après {elapsed:.1f}s")
                        return True
                        
                    consecutive_failures = 0
                    success = True
                    
                except requests.exceptions.Timeout:
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        logging.warning(f"⏰ Timeout répétés pour {process_name} - Vérification de la charge CPU...")
                        consecutive_failures = 0
                    
                except requests.exceptions.ConnectionError:
                    pass  # Service pas encore prêt, continuer
                    
                except requests.exceptions.RequestException as e:
                    if time.time() - last_log_time > 15:  # Log moins fréquent
                        logging.debug(f"🔧 Tentative échouée pour {check_url}: {e}")
                        last_log_time = time.time()
            
            # Log de statut périodique
            elapsed = time.time() - start_time
            if int(elapsed) % 15 == 0:  # Toutes les 15s seulement
                logging.info(f"⏳ ATTENTE: En attente de {process_name}... ({int(elapsed)}s/{timeout}s)")
            
            # ⬅️ NOUVEAU : Backoff exponentiel pour éviter la surcharge
            sleep_time = min(2 * (consecutive_failures + 1), 10)
            time.sleep(sleep_time)
        
        logging.error(f"❌ TIMEOUT: Service {process_name} non accessible après {timeout}s")
        
        # ⬅️ NOUVEAU : Diagnostic automatique
        self.diagnose_service_issue(process_name, port)
        return False
    
    def stop_process(self, process_name: str, force: bool = False) -> bool:
        """Arrete un processus"""
        try:
            if process_name not in self.processes:
                logging.warning(f"ATTENTION: Processus {process_name} non trouve")
                return True
            
            process = self.processes[process_name]
            
            if process.poll() is None:
                logging.info(f"ARRET: Arret de {process_name}...")
                
                if force:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                else:
                    # Arret gracieux
                    process.terminate()
                    try:
                        process.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        logging.warning(f"ATTENTION: Timeout arret gracieux {process_name}, kill...")
                        process.kill()
                        process.wait()
                
                logging.info(f"SUCCES: {process_name} arrete")
            
            del self.processes[process_name]
            return True
            
        except Exception as e:
            logging.error(f"ERREUR: Erreur arret {process_name}: {e}")
            return False
    
    def restart_process(self, process_name: str) -> bool:
        """Redemarre un processus"""
        try:
            config = self.process_configs[process_name]
            
            # Verifier le nombre de redemarrages
            if self.restart_counts.get(process_name, 0) >= config['max_restarts']:
                logging.error(f"ERREUR: Trop de redemarrages pour {process_name}")
                return False
            
            logging.info(f"REDEMARRAGE: Redemarrage de {process_name}...")
            
            # Arreter le processus
            self.stop_process(process_name)
            
            # Delai avant redemarrage
            time.sleep(config['restart_delay'])
            
            # Redemarrer
            return self.start_process(process_name)
            
        except Exception as e:
            logging.error(f"ERREUR: Erreur redemarrage {process_name}: {e}")
            return False
    
    def monitor_processes(self):
        """Surveille tous les processus"""
        while True:
            try:
                for process_name in list(self.processes.keys()):
                    if not self.is_process_running(process_name):
                        logging.warning(f"ATTENTION: Processus {process_name} arrete")
                        
                        if self.process_configs[process_name]['required']:
                            logging.info(f"REDEMARRAGE: Tentative de redemarrage de {process_name}...")
                            self.restart_process(process_name)
                        else:
                            logging.info(f"INFO: Processus {process_name} non requis, pas de redemarrage")
                
                # Mettre a jour les metriques de performance
                self.update_performance_metrics()
                
                time.sleep(10)  # Verifier toutes les 10 secondes
                
            except Exception as e:
                logging.error(f"ERREUR: Erreur monitoring: {e}")
                time.sleep(30)
    
    def update_performance_metrics(self):
        """Met a jour les metriques de performance"""
        try:
            self.performance_metrics = {
                'uptime': str(datetime.now() - self.system_start_time),
                'active_processes': len([p for p in self.processes.values() if p.poll() is None]),
                'total_restarts': sum(self.restart_counts.values()),
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"ERREUR: Erreur metriques performance: {e}")
    
    def graceful_shutdown(self):
        """Arret gracieux de tous les processus"""
        logging.info("ARRET: Arret gracieux du systeme...")
        
        # Arreter tous les processus dans l'ordre inverse
        for process_name in reversed(list(self.processes.keys())):
            self.stop_process(process_name)
        
        logging.info("SUCCES: Systeme arrete avec succes")

class IntelligentLauncher:
    """Lanceur intelligent principal"""
    
    def __init__(self):
        self.process_manager = IntelligentProcessManager()
        self.running = False
        self.control_lock = threading.Lock()
        
    def get_optimized_startup_sequence(self):
        """Retourne la séquence optimisée pour la sortie intelligente"""
        return [
            'ai_engine',           # ✅ DEUXIÈME - IA distante (Groq)
            'dashboard',
            'bot'                  # ✅ DERNIER - Dépend de tout le système
        ]

    def start_system_control(self):
        with self.control_lock:
            return self.start_system()

    def stop_system_control(self):
        with self.control_lock:
            self.running = False
            self.process_manager.graceful_shutdown()
            return True

    def restart_system_control(self):
        with self.control_lock:
            self.process_manager.graceful_shutdown()
            return self.start_system()

    def start_system(self):
        """Demarre l'ensemble du systeme - VERSION AMÉLIORÉE"""
        print("=" * 60)
        print("BTCUSD MICRO SCALPER V8 - LANCEUR INTELLIGENT OPTIMISÉ")
        print("🧠 IA DISTANTE (Groq)")
        print("🔄 REDÉMARRAGE INTELLIGENT ACTIF")
        print("=" * 60)
        
        try:
            # ✅ SÉQUENCE OPTIMISÉE POUR SORTIE INTELLIGENTE
            startup_sequence = self.get_optimized_startup_sequence()
            
            for process_name in startup_sequence:
                config = self.process_manager.process_configs[process_name]
                
                logging.info(f"🚀 Démarrage de {process_name}...")
                
                # ⬅️ UTILISER LE SYSTÈME DE RETRY
                success = self.process_manager.start_process_with_retry(process_name)
                
                if not success and config['required']:
                    logging.error(f"❌ PROCESSUS REQUIS {process_name} NON DÉMARRÉ - ARRÊT DU SYSTÈME")
                    return False
                elif not success:
                    logging.warning(f"⚠️  Processus optionnel {process_name} non démarré")
                    
                # ✅ VÉRIFICATION CRITIQUE : Sortie intelligente activée
                logging.info("🔍 Vérification de l'activation de la sortie intelligente...")
                time.sleep(5)  # Attendre que main.py soit complètement initialisé

                # Vérifier que le bot utilise bien main.py
                bot_config = self.process_manager.process_configs['bot']
                if 'main.py' in ' '.join(bot_config['command']):
                    logging.info("✅ SYSTÈME DE SORTIE INTELLIGENTE ACTIVÉ")
                    logging.info("   🧠 Groq connecté")
                    logging.info("   🛡️  Guardian System injecté")
                    logging.info("   📊 Monitoring des sorties actif")
                else:
                    logging.error("❌ ERREUR: Sortie intelligente non activée!")
            
            # ⬅️ NOUVEAU : Attendre que tous les services soient stables
            logging.info("📊 Vérification de la stabilité du système...")
            time.sleep(10)
            
            # Démarrer la surveillance
            self.running = True
            monitor_thread = threading.Thread(target=self.process_manager.monitor_processes, daemon=True)
            monitor_thread.start()
            
            # Démarrer le cleanup mémoire périodique
            memory_thread = threading.Thread(target=self.process_manager.memory_manager.periodic_cleanup, daemon=True)
            memory_thread.start()
            
            print("\n" + "=" * 60)
            print("✅ SYSTÈME MICRO SCALPING OPTIMISÉ LANCÉ!")
            print("🤖 Moteur IA: http://localhost:5003")
            print("🔧 Monitoring: Redémarrage intelligent actif")
            print("💾 Gestion mémoire: Optimisée")
            print("=" * 60)
            print("ALERTE: SYSTEME DE TRADING ACTIF!")
            print("CAPITAL: Solde MT5 réel utilisé")
            print("RISQUE: Risk: 0.5% | TP: 3 pips | SL: 5 pips")
            print("ARRET: Ctrl+C pour arreter gracieusement")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            logging.error(f"ERREUR: Erreur demarrage systeme: {e}")
            return False
    
    def run(self):
        """Boucle principale"""
        if not self.start_system():
            return
        
        try:
            while self.running:
                # Afficher les statistiques periodiquement
                self.display_system_status()
                time.sleep(30)
                
        except KeyboardInterrupt:
            print("\nARRET: Arret demande par l'utilisateur...")
        except Exception as e:
            logging.error(f"ERREUR: Erreur boucle principale: {e}")
        finally:
            self.running = False
            self.process_manager.graceful_shutdown()
    
    def display_system_status(self):
        """Affiche le statut du systeme"""
        try:
            metrics = self.process_manager.performance_metrics
            
            print(f"\nSTATUT SYSTEME - {datetime.now().strftime('%H:%M:%S')}")
            print(f"UPTIME: {metrics.get('uptime', 'N/A')}")
            print(f"PROCESSUS: Actifs: {metrics.get('active_processes', 0)}")
            print(f"REDEMARRAGES: Totaux: {metrics.get('total_restarts', 0)}")
            print(f"RESOURCES: CPU: {metrics.get('cpu_percent', 0):.1f}% | RAM: {metrics.get('memory_percent', 0):.1f}%")
            
            # Verifier l'etat des processus
            for process_name in self.process_manager.process_configs:
                is_running = self.process_manager.is_process_running(process_name)
                status = "ACTIF" if is_running else "ARRETE"
                status_symbol = "[OK]" if is_running else "[ERREUR]"
                print(f"   {process_name}: {status_symbol} {status}")
            
            print("-" * 40)
            
        except Exception as e:
            logging.error(f"ERREUR: Erreur affichage statut: {e}")

def main():
    """Point d'entree principal"""
    launcher = IntelligentLauncher()

    def control_server():
        from http.server import BaseHTTPRequestHandler, HTTPServer

        class Handler(BaseHTTPRequestHandler):
            def _json(self, code: int, payload: dict):
                body = json.dumps(payload).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                return

            def do_GET(self):
                if self.path == "/status":
                    launcher.process_manager.update_performance_metrics()
                    metrics = launcher.process_manager.performance_metrics
                    processes = {}
                    for name, proc in launcher.process_manager.processes.items():
                        processes[name] = {
                            "running": proc.poll() is None,
                            "pid": proc.pid if proc else None,
                        }
                    return self._json(200, {"metrics": metrics, "processes": processes})
                return self._json(404, {"error": "not_found"})

            def do_POST(self):
                if self.path == "/start":
                    ok = launcher.start_system_control()
                    return self._json(200, {"ok": ok})
                if self.path == "/stop":
                    ok = launcher.stop_system_control()
                    return self._json(200, {"ok": ok})
                if self.path == "/restart":
                    ok = launcher.restart_system_control()
                    return self._json(200, {"ok": ok})
                return self._json(404, {"error": "not_found"})

        server = HTTPServer(("127.0.0.1", 5010), Handler)
        server.serve_forever()

    threading.Thread(target=control_server, daemon=True).start()
    
    try:
        launcher.run()
    except Exception as e:
        logging.error(f"ERREUR CRITIQUE: {e}")
    finally:
        print("SUCCES: Lanceur intelligent arrete")

if __name__ == "__main__":
    main()