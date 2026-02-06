# main.py
#!/usr/bin/env python3
"""
POINT D'ENTRÉE PRINCIPAL - BTCUSD MICRO SCALPER V8
Système de trading professionnel avec gestion intelligente
"""

import sys
import os
import argparse
from datetime import datetime
import threading
import requests 
from dotenv import load_dotenv

# Ajout du chemin des modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.utils import setup_global_logger, get_logger
from backend.core import initialize_engine
from backend.config import Config, INTELLIGENT_EXIT_CONFIG, GUARDIAN_SYSTEM_CONFIG

def parse_arguments():
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(description='BTCUSD Micro Scalper V8 Pro')
    
    parser.add_argument('--mode', 
                       choices=['REAL'], 
                       default='REAL',
                       help='Mode de trading (réel uniquement)')
    
    parser.add_argument('--strategy',
                       choices=['MICRO', 'SCALPING', 'SWING'],
                       default='MICRO',
                       help='Stratégie de trading (défaut: MICRO)')
    
    
    parser.add_argument('--ai-engine',
                       action='store_true',
                       default=False,
                       help='Activer le moteur IA adaptatif (défaut: False)')
                       
    # ✅ CORRECTION: Sortie intelligente ACTIVÉE par défaut
    parser.add_argument('--no-intelligent-exit',
                       action='store_true',
                       default=False,
                       help='DÉSACTIVER le système de sortie intelligente (défaut: ACTIVÉ)')
    
    parser.add_argument('--risk',
                       type=float,
                       default=0.5,
                       help='Risque par trade %% (défaut: 0.5%%)')
    
    parser.add_argument('--capital',
                       type=float,
                       help='Capital initial ($) (défaut: $1000)')
    
    return parser.parse_args()
    
def setup_environment():
    """Configure l'environnement de trading"""
    load_dotenv()
    print("=" * 60)
    print("🎯 BTCUSD MICRO SCALPER V8 - SYSTÈME PROFESSIONNEL")
    print("💰 MODE MICRO SCALPING AVANCÉ")
    print("🧠 IA ADAPTATIVE & GESTION DES RISQUES")
    print("=" * 60)
    
    # Configuration du logger global
    logger = setup_global_logger(
        name="BTCUSD_Micro_Scalper_V8",
        log_dir="logs",
        enable_console=True,
        enable_file=True,
        enable_json=True
    )

    return logger

def initialize_trading_system(mode: str, strategy: str, risk: float, capital: float = None, intelligent_exit: bool = True):
    """Initialise le système de trading"""
    logger = get_logger()
    
    try:
        # ✅ CORRECTION: Import sécurisé de la config
        try:
            from backend.config import Config, INTELLIGENT_EXIT_CONFIG, GUARDIAN_SYSTEM_CONFIG
        except ImportError as e:
            logger.error(f"❌ Impossible d'importer la configuration: {e}")
            # Config de secours
            class Config:
                TRADING_MODE = 'PAPER'
                RISK_PER_TRADE = 0.5
                INITIAL_CAPITAL = 1000.0
                MICRO_SCALPING_ENABLED = False
                SCALPING_ENABLED = False
                SWING_TRADING_ENABLED = False
                INTELLIGENT_EXIT_ENABLED = False
            
            INTELLIGENT_EXIT_CONFIG = {'exit_probability_threshold': 0.75, 'no_fixed_sl_tp': True}
            GUARDIAN_SYSTEM_CONFIG = {'enabled': True, 'monitoring_factors': {}}
        
        # Créer l'instance de configuration
        config = Config()
        
        # Ajustement selon le mode
        if mode != 'REAL':
            raise RuntimeError("Mode non autorisé: REAL uniquement")

        config.TRADING_MODE = 'REAL'
        config.RISK_PER_TRADE = risk
        logger.warning("🚨 MODE RÉEL ACTIVÉ - TRADING AVEC ARGENT RÉEL!")
        
        # Ajustement stratégie
        if strategy == 'MICRO':
            config.MICRO_SCALPING_ENABLED = True
            config.MAX_MICRO_TRADES_PER_DAY = 100
            logger.info("⚡ STRATÉGIE MICRO-SCALPING ACTIVÉE")
        elif strategy == 'SCALPING':
            config.SCALPING_ENABLED = True
            logger.info("📈 STRATÉGIE SCALPING ACTIVÉE")
        else:
            config.SWING_TRADING_ENABLED = True
            logger.info("📊 STRATÉGIE SWING TRADING ACTIVÉE")
            
        # ✅ AJOUT: Configuration sortie intelligente
        if intelligent_exit:
            config.INTELLIGENT_EXIT_ENABLED = True
            logger.info("🎯 SYSTÈME DE SORTIE INTELLIGENTE ACTIVÉ")
            logger.info(f"   📊 Seuil probabilité: {INTELLIGENT_EXIT_CONFIG['exit_probability_threshold']}")
            logger.info(f"   🛡️  Guardian System: {'ACTIVÉ' if GUARDIAN_SYSTEM_CONFIG['enabled'] else 'DÉSACTIVÉ'}")
            logger.info(f"   ⚡ Pas de SL/TP fixes: {INTELLIGENT_EXIT_CONFIG['no_fixed_sl_tp']}")
        else:
            config.INTELLIGENT_EXIT_ENABLED = False
            logger.warning("⚠️  Système de sortie intelligente désactivé")
        
        # Capital personnalisé
        if capital:
            config.INITIAL_CAPITAL = capital
            logger.info(f"💰 Capital personnalisé: ${capital:.2f}")
        else:
            config.INITIAL_CAPITAL = 1000.0  # Valeur par défaut
        
        # ✅ CONNEXION MT5 RÉELLE (obligatoire)
        logger.info("🔗 Tentative de connexion MT5 RÉELLE...")
        try:
            import MetaTrader5 as mt5

            mt5_login = os.getenv("MT5_LOGIN")
            mt5_password = os.getenv("MT5_PASSWORD")
            mt5_server = os.getenv("MT5_SERVER")

            if not mt5_login or not mt5_password or not mt5_server:
                raise RuntimeError("Variables MT5_LOGIN, MT5_PASSWORD, MT5_SERVER obligatoires")

            mt5_login = int(mt5_login)

            if not mt5.initialize():
                error_msg = mt5.last_error()
                logger.error(f"❌ Échec initialisation MT5: {error_msg}")
                raise Exception(f"MT5 initialization failed: {error_msg}")

            if not mt5.login(mt5_login, mt5_password, mt5_server):
                error_msg = mt5.last_error()
                logger.error(f"❌ Échec connexion MT5: {error_msg}")
                raise Exception(f"MT5 login failed: {error_msg}")

            account_info = mt5.account_info()
            if account_info:
                logger.info("✅ CONNEXION MT5 RÉELLE RÉUSSIE!")
                logger.info(f"   📊 Compte: {mt5_login}")
                logger.info(f"   💰 Balance: {account_info.balance:.2f} {account_info.currency}")
                logger.info(f"   🏦 Broker: {mt5_server}")
                logger.info(f"   📈 Effet de levier: 1:{account_info.leverage}")
            else:
                logger.warning("⚠️  Connexion MT5 réussie mais infos compte non disponibles")

            class RealMT5Engine:
                def __init__(self):
                    self.simulation_mode = False
                    self.connected = True
                    self.login = mt5_login
                    self.server = mt5_server

                def ensure_connection(self):
                    """Vérifie et maintient la connexion MT5"""
                    try:
                        if not mt5.initialize():
                            logger.warning("🔄 Reconnexion MT5...")
                            if mt5.initialize() and mt5.login(mt5_login, mt5_password, mt5_server):
                                logger.info("✅ Reconnexion MT5 réussie")
                                return True
                            return False
                        return True
                    except Exception as e:
                        logger.error(f"❌ Erreur vérification connexion MT5: {e}")
                        return False

                def shutdown(self):
                    """Ferme la connexion MT5"""
                    try:
                        mt5.shutdown()
                        logger.info("🔌 Connexion MT5 fermée")
                    except Exception as e:
                        logger.error(f"❌ Erreur fermeture MT5: {e}")

            mt5_engine = RealMT5Engine()

        except ImportError:
            logger.error("❌ MetaTrader5 non installé - Exécute: 'pip install MetaTrader5'")
            raise
        except Exception as e:
            logger.error(f"❌ Erreur connexion MT5 réelle: {e}")
            logger.error("💡 Vérifie tes identifiants MT5 et que la plateforme est ouverte")
            raise
        
        logger.info("✅ Système de trading initialisé avec succès")
        return config, mt5_engine
        
    except Exception as e:
        logger.error(f"💥 Erreur initialisation système: {e}")
        return None
        
def start_exit_system_monitoring(guardian_system, interval_seconds=30):
    """Démarre le monitoring en temps réel du système de sortie"""
    def monitoring_loop():
        logger = get_logger()
        while True:
            try:
                ok = check_ai_engine_connection()
                if not ok:
                    logger.warning("⚠️ IA Engine indisponible (monitoring)")
                
                # Attendre avant prochaine vérification
                threading.Event().wait(interval_seconds)
                
            except Exception as e:
                logger.error(f"❌ Erreur monitoring sortie: {e}")
                threading.Event().wait(interval_seconds)
    
    # Démarrer le thread de monitoring
    monitor_thread = threading.Thread(target=monitoring_loop, daemon=True)
    monitor_thread.start()
    get_logger().info(f"📊 Monitoring sortie intelligente démarré (intervalle: {interval_seconds}s)")


def start_ai_engine():
    """Démarre le moteur IA adaptatif"""
    try:
        from backend.ai.adaptive_engine import run_ai_server
        
        logger = get_logger()
        logger.info("🧠 Démarrage du moteur IA Groq...")
        
        thread = threading.Thread(target=run_ai_server, daemon=True)
        thread.start()
        logger.info("✅ Moteur IA Groq démarré")
        return thread
        
    except Exception as e:
        get_logger().error(f"❌ Erreur démarrage moteur IA: {e}")
        return None
        
def check_ai_engine_connection():
    """Vérifie la connexion à l'IA Engine de manière robuste"""
    try:
        import requests
        response = requests.get('http://localhost:5003/api/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get('status') == 'healthy'
        return False
    except Exception as e:
        get_logger().warning(f"⚠️ IA Engine temporairement indisponible: {e}")
        # Mode dégradé mais continuer
        return False

def main():
    """Fonction principale"""
    args = parse_arguments()
    logger = setup_environment()
    
    try:
        # ✅ AJOUT: Vérification des imports critiques
        try:
            from backend.bots.bot_btcusd_ultra_scalper_v8_clean import BTCUSDMicroScalperPro
        except ImportError as e:
            logger.error(f"❌ Impossible d'importer le bot principal: {e}")
            logger.error("💡 Vérifiez que le fichier backend/bots/bot_btcusd_ultra_scalper_v8_clean.py existe")
            return 1
        
        # ✅ CORRECTION: Sortie intelligente ACTIVÉE par défaut
        intelligent_exit_enabled = not args.no_intelligent_exit
        
        # Affichage informations système
        logger.info("=" * 60)
        logger.info("🎯 CONFIGURATION SYSTÈME - BTCUSD MICRO SCALPER V8")
        logger.info("=" * 60)
        logger.info(f"📋 Mode: {args.mode}")
        logger.info(f"🎯 Stratégie: {args.strategy}")
        logger.info(f"⚡ Risk/Trade: {args.risk}%")
        logger.info(f"🧠 Sortie intelligente: {'✅ ACTIVÉE' if intelligent_exit_enabled else '❌ DÉSACTIVÉE'}")
        logger.info(f"🤖 IA Engine: {'✅ ACTIVÉ' if args.ai_engine else '❌ DÉSACTIVÉ'}")
        logger.info(f"💰 Capital: ${args.capital if args.capital else 1000:.2f}")
        logger.info("=" * 60)
        logger.info(f"🐍 Python: {sys.version.split()[0]}")
        logger.info(f"📁 Répertoire: {os.getcwd()}")
        
        # Initialisation système trading
        system_config = initialize_trading_system(
            mode=args.mode,
            strategy=args.strategy,
            risk=args.risk,
            capital=args.capital,
            intelligent_exit=intelligent_exit_enabled  # ✅ UTILISER LA VARIABLE CORRECTE
        )
        
        if not system_config:
            logger.error("❌ Échec initialisation système trading")
            return 1
        
        config, mt5_engine = system_config
        
        
        # Démarrage moteur IA si demandé
        ai_engine = None
        if args.ai_engine:
            logger.info("🧠 Moteur IA: externe (lanceur) — vérification connexion...")
            ai_engine = check_ai_engine_connection()
            if ai_engine:
                logger.info("✅ Moteur IA adaptatif opérationnel")
            else:
                logger.warning("⚠️ Moteur IA non disponible")
        else:
            logger.info("🧠 Moteur IA: Non demandé")
        
        # Démarrage du bot principal
        logger.info("🤖 Démarrage du bot Micro Scalper V8...")
        
        bot = BTCUSDMicroScalperPro()
        
        # Configuration finale
        logger.info("=" * 60)
        logger.info("✅ SYSTÈME COMPLET INITIALISÉ AVEC SUCCÈS!")
        logger.info("=" * 60)
        logger.info(f"💰 Capital: ${config.INITIAL_CAPITAL:.2f}")
        logger.info(f"⚡ Risk/Trade: {config.RISK_PER_TRADE}%")
        logger.info(f"📈 Stratégie: {args.strategy}")
        logger.info(f"🎯 Mode: {args.mode}")
        logger.info(f"🧠 IA: {'✅ ACTIF' if ai_engine else '❌ INACTIF'}")
        logger.info("🛡️  Sortie intelligente: pilotée par Groq")
        logger.info("=" * 60)
        logger.info("🚀 Démarrage des opérations de trading...")

        # Démarrage du bot
        bot.run()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("🛑 Arrêt demandé par l'utilisateur")
        return 0
    except Exception as e:
        logger.critical(f"💥 ERREUR CRITIQUE: {e}")
        import traceback
        logger.critical(f"📋 Stack trace: {traceback.format_exc()}")
        return 1
    finally:
        # Nettoyage
        try:
            if 'mt5_engine' in locals():
                mt5_engine.shutdown()
                logger.info("🔌 Connexion MT5 fermée")
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de la fermeture MT5: {e}")
        
        logger.info("✅ Système arrêté avec succès")
        
if __name__ == "__main__":
    sys.exit(main())