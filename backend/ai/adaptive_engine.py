# ai/adaptive_engine.py CORRIGÉ - VERSION SÉCURISÉE MULTI-THREAD
"""
MOTEUR IA ADAPTATIF AVEC SERVEUR WEB - BTCUSD MICRO SCALPER V8
Version sécurisée avec gestion multi-thread SQLite
"""

from flask import Flask, jsonify
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional, Tuple
import json
import threading
import time
from dataclasses import dataclass
from enum import Enum
import sqlite3
import os
import importlib
import random
import requests
import psutil
from flask import request
import MetaTrader5 as mt5
import gc 

import sys
from pathlib import Path

# Assurer l'import des modules backend quand lancé en script
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from backend.ai.groq_service import GroqService

# Verrou global pour la base de données
db_lock = threading.Lock()

class MarketRegime(Enum):
    """Régimes de marché"""
    TRENDING_BULL = "TRENDING_BULL"
    TRENDING_BEAR = "TRENDING_BEAR"
    RANGING = "RANGING"
    VOLATILE = "VOLATILE"
    CALM = "CALM"

class SignalDirection(Enum):
    """Directions des signaux"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

@dataclass
class TradingSignal:
    """Signal de trading généré par l'IA"""
    symbol: str
    direction: SignalDirection
    confidence: float
    price: float
    timestamp: datetime
    features: Dict[str, float]
    model_version: str
    regime: MarketRegime

class AdaptiveAIEngine:
    """
    Moteur IA adaptatif avec apprentissage en temps réel
    Version sécurisée multi-thread
    """
    
    def __init__(self, model_version: str = "v1.0"):
        self.model_version = model_version
        self.is_training = False
        self.market_regime = MarketRegime.RANGING
        self.performance_history = []
        
        # Configuration logging
        self.logger = logging.getLogger('AI_Engine')

        # ✅ CLIENT GROQ (IA distante)
        self.groq = GroqService(logger=self.logger)
        
        # ✅ INITIALISATION MT5
        self.mt5_initialized = self.initialize_mt5()
        
        # ✅ VARIABLES POUR LIMITATION D'APPELS
        self._last_brain_call = 0
        self._consecutive_brain_errors = 0
        self._brain_cooldown_until = 0
        
        # ✅ CACHE POUR PERFORMANCE
        self.signal_cache = {}
        self.cache_timeout = 5  # secondes
        self.last_evolutionary_success = None
        
        # Base de données pour l'apprentissage
        self.setup_database()
        
        # Métriques de performance
        self.performance_metrics = {
            'total_predictions': 0,
            'correct_predictions': 0,
            'accuracy': 0.0,
            'last_training': None,
            'model_confidence': 0.5,
            'brain_success_rate': 0.0,
            'brain_total_calls': 0,
            'brain_successful_calls': 0
        }
        
        # Thread de mise à jour
        self.update_thread = threading.Thread(target=self._update_worker, daemon=True)
        self.running = False
        self._cleanup_counter = 0
        self._consecutive_brain_errors = 0
        self._last_brain_error = 0
        
        self.logger.info(f"[MOTEUR] 🔥 MOTEUR IA VERSION CORRIGÉE {model_version} - THREAD-SAFE ACTIF")
        
        self.signal_cache = {}
        self.cache_timeout = 5  # secondes
        self.last_evolutionary_success = None
        
    def initialize_mt5(self):
        """Initialise la connexion à MetaTrader 5"""
        try:
            if not mt5.initialize():
                self.logger.warning("❌ MT5 non initialisé - Fallback sans données marché")
                return False
                
            # ✅ VÉRIFIER QUE LA CONNEXION FONCTIONNE
            symbol_info = mt5.symbol_info("BTCUSD")
            if symbol_info is None:
                self.logger.warning("❌ Symbole BTCUSD non disponible dans MT5")
                mt5.shutdown()
                return False
            
            self.logger.info("✅ MT5 initialisé avec succès")
            return True
            
        except Exception as e:
            self.logger.warning(f"⚠️ MT5 non disponible: {e} - Fallback activé")
            return False
        
    def _cleanup_cache(self):
        """Nettoie le cache des signaux expirés"""
        try:
            current_time = time.time()
            expired_keys = [
                key for key in self.signal_cache 
                if current_time - int(key.split('_')[-1]) * 10 > self.cache_timeout
            ]
            for key in expired_keys:
                del self.signal_cache[key]
        except Exception as e:
            self.logger.debug(f"Cache cleanup: {e}")
        
    def _safe_db_operation(self, operation, *args, max_retries=3):
        """Exécute une opération BDD avec reprise sur erreur"""
        for attempt in range(max_retries):
            try:
                with db_lock:
                    return operation(*args)
            except sqlite3.OperationalError as e:
                if "locked" in str(e) and attempt < max_retries - 1:
                    time.sleep(0.1 * (attempt + 1))
                    continue
                else:
                    raise e
        
    def _update_worker(self):
        """Tâche de mise à jour en arrière-plan (thread-safe)"""
        while self.running:
            try:
                import gc 
                
                # ✅ RÉDUIRE LA FRÉQUENCE (toutes les 2 minutes)
                time.sleep(120)
                
                # ✅ NETTOYAGE MÉMOIRE PÉRIODIQUE
                self._cleanup_counter += 1
                if self._cleanup_counter % 3 == 0:  # Toutes les 6 minutes
                    gc.collect()
                    memory_percent = psutil.Process().memory_percent()
                    if memory_percent > 75:
                        self.logger.warning(f"🧹 Nettoyage mémoire - RAM: {memory_percent:.1f}%")
                    
                # IA interne désactivée (Groq uniquement) : pas de génération/entrainement local
                self._cleanup_old_data_thread_safe()
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"[ERREUR] Erreur worker IA: {e}")
                time.sleep(60)
                
    def setup_database(self):
        """Initialise la base de données d'apprentissage de manière thread-safe"""
        try:
            # Connexion thread-safe
            self.conn = sqlite3.connect('ai_training.db', timeout=30, check_same_thread=False)
            cursor = self.conn.cursor()
            
            # Table des features
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    symbol TEXT,
                    price REAL,
                    rsi REAL,
                    volatility REAL,
                    volume_ratio REAL,
                    trend_strength REAL,
                    market_regime TEXT,
                    price_change_5m REAL,
                    price_change_15m REAL,
                    price_change_1h REAL
                )
            ''')
            
            # Table des signaux
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    symbol TEXT,
                    direction TEXT,
                    confidence REAL,
                    price REAL,
                    features TEXT,
                    model_version TEXT,
                    executed BOOLEAN DEFAULT FALSE,
                    profit REAL,
                    success BOOLEAN
                )
            ''')
            
            # Table performance modèle
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    model_version TEXT,
                    accuracy REAL,
                    total_predictions INTEGER,
                    correct_predictions INTEGER,
                    training_duration REAL
                )
            ''')
            
            self.conn.commit()
            self.logger.info("[OK] Base de données IA initialisée (thread-safe)")
            
        except Exception as e:
            self.logger.error(f"[ERREUR] Erreur initialisation base de données IA: {e}")
    
    def start(self):
        """Démarre le moteur IA"""
        self.running = True
        self.update_thread.start()
        self.logger.info(">>> Moteur IA démarré (thread-safe)")
    
    def stop(self):
        """Arrête le moteur IA"""
        self.running = False
        if hasattr(self, 'conn'):
            with db_lock:
                self.conn.close()
        self.logger.info("[ARRET] Moteur IA arrêté")
    
    def analyze_market(self, market_data: Dict) -> TradingSignal:
        """
        Analyse le marché et génère un signal de trading
        Version thread-safe
        """
        raise RuntimeError("analyse_market désactivé: utiliser /api/decision (Groq uniquement)")
            
    def analyze_market_robust(self, market_data: Dict) -> TradingSignal:
        """Version robuste de l'analyse de marché"""
        raise RuntimeError("analyze_market_robust désactivé: Groq uniquement")
    
    def _extract_features(self, market_data: Dict) -> Dict[str, float]:
        """Extrait les features du marché"""
        # Implémentation simplifiée - à enrichir avec de vraies features
        return {
            'rsi': market_data.get('rsi', 50),
            'volatility': market_data.get('volatility', 0.01),
            'price': market_data.get('bid', 0),
            'spread': market_data.get('spread', 0),
            'volume': market_data.get('volume', 0),
            'trend_strength': np.random.random(),
            'momentum': np.random.normal(0, 1),
            'support_distance': np.random.random(),
            'resistance_distance': np.random.random()
        }
    
    def _detect_market_regime(self, features: Dict) -> MarketRegime:
        """Détecte le régime de marché actuel"""
        rsi = features.get('rsi', 50)
        volatility = features.get('volatility', 0.01)
        trend_strength = features.get('trend_strength', 0.5)
        
        if volatility > 0.03:
            return MarketRegime.VOLATILE
        elif volatility < 0.01:
            return MarketRegime.CALM
        elif trend_strength > 0.7 and rsi > 60:
            return MarketRegime.TRENDING_BULL
        elif trend_strength > 0.7 and rsi < 40:
            return MarketRegime.TRENDING_BEAR
        else:
            return MarketRegime.RANGING
    
    def _generate_signal(self, features: Dict) -> TradingSignal:
        """Version avec IA évolutive progressive"""
        raise RuntimeError("_generate_signal désactivé: Groq uniquement")

    def _generate_ai_evolutionary_signal(self, features: Dict) -> TradingSignal:
        """Utilise Groq (IA distante) avec COOLDOWN INTELLIGENT"""
        raise RuntimeError("_generate_ai_evolutionary_signal désactivé: Groq uniquement")
                
    def call_evolutionary_brain_with_retry(self, market_data, max_retries=2, timeout=5):
        """Appel robuste à Groq avec retry et timeout OPTIMISÉ"""
        raise RuntimeError("call_evolutionary_brain_with_retry désactivé: Groq uniquement via /api/decision")
        
    def call_evolutionary_brain_fast(self, market_data, max_retries=2, timeout=3):
        """Appel RAPIDE et OPTIMISÉ à Groq"""
        raise RuntimeError("call_evolutionary_brain_fast désactivé: Groq uniquement via /api/decision")
                        
    def _generate_fallback_signal(self, features: Dict) -> TradingSignal:
        """Signal de secours AVEC CHANDELIERS MT5 - VERSION CORRIGÉE"""
        raise RuntimeError("_generate_fallback_signal désactivé: aucun fallback autorisé")

    def _analyze_candles_directly(self, df: pd.DataFrame) -> Dict:
        """Analyse les chandeliers directement sans dépendance externe"""
        try:
            if len(df) < 3:
                return {'composite_score': 0, 'signal_strength': 0, 'patterns': []}
            
            patterns = []
            composite_score = 0
            signal_strength = 0
            
            # Analyser les 3 derniers chandeliers
            for i in range(max(0, len(df)-3), len(df)-1):
                current = df.iloc[i]
                previous = df.iloc[i-1] if i > 0 else current
                
                # Calculer les caractéristiques du chandelier
                body_size = abs(current['close'] - current['open'])
                total_range = current['high'] - current['low']
                body_ratio = body_size / total_range if total_range > 0 else 0
                
                # Détection de patterns simples
                is_bullish = current['close'] > current['open']
                is_strong = body_ratio > 0.6
                
                # Pattern: Chandelier haussier fort
                if is_bullish and is_strong:
                    patterns.append({'name': 'BULLISH_STRONG', 'strength': 0.8})
                    composite_score += 0.3
                    signal_strength += 0.8
                    
                # Pattern: Chandelier baissier fort  
                elif not is_bullish and is_strong:
                    patterns.append({'name': 'BEARISH_STRONG', 'strength': 0.8})
                    composite_score -= 0.3
                    signal_strength += 0.8
                    
                # Pattern: Doji (indécis)
                elif body_ratio < 0.1:
                    patterns.append({'name': 'DOJI', 'strength': 0.1})
                    composite_score += 0
                    signal_strength += 0.1
            
            # Normaliser les scores
            if patterns:
                composite_score = max(-1, min(1, composite_score))
                signal_strength = max(0, min(1, signal_strength / len(patterns)))
            
            return {
                'composite_score': composite_score,
                'signal_strength': signal_strength,
                'patterns': patterns
            }
            
        except Exception as e:
            self.logger.error(f"Erreur analyse chandeliers: {e}")
            return {'composite_score': 0, 'signal_strength': 0, 'patterns': []}

    def _generate_rsi_fallback(self, features: Dict) -> TradingSignal:
        """Fallback basé sur RSI uniquement"""
        raise RuntimeError("_generate_rsi_fallback désactivé: aucun fallback autorisé")

    def _generate_neutral_signal(self, market_data: Dict) -> TradingSignal:
        """Génère un signal neutre (fallback)"""
        raise RuntimeError("_generate_neutral_signal désactivé: aucun fallback autorisé")
    
    def _save_features_thread_safe(self, features: Dict, market_data: Dict):
        """Sauvegarde les features en base de manière thread-safe"""
        try:
            def save_operation():
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO market_features 
                    (timestamp, symbol, price, rsi, volatility, volume_ratio, trend_strength, market_regime)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    "BTCUSD",
                    market_data.get('bid', 0),
                    features.get('rsi', 50),
                    features.get('volatility', 0.01),
                    features.get('volume_ratio', 1),
                    features.get('trend_strength', 0.5),
                    self.market_regime.value
                ))
                self.conn.commit()
                self.logger.debug("[OK] Features sauvegardées (thread-safe)")
            
            self._safe_db_operation(save_operation)
            
        except Exception as e:
            self.logger.error(f"[ERREUR] Erreur sauvegarde features: {e}")
    
    def _save_signal_thread_safe(self, signal: TradingSignal):
        """Sauvegarde le signal en base de manière thread-safe"""
        try:
            def save_operation():
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO ai_signals 
                    (timestamp, symbol, direction, confidence, price, features, model_version)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal.timestamp,
                    signal.symbol,
                    signal.direction.value,
                    signal.confidence,
                    signal.price,
                    json.dumps(signal.features),
                    signal.model_version
                ))
                self.conn.commit()
                self.logger.debug("[OK] Signal sauvegardé (thread-safe)")
            
            self._safe_db_operation(save_operation)
            
        except Exception as e:
            self.logger.error(f"[ERREUR] Erreur sauvegarde signal: {e}")
            
    def check_brain_health(self):
        """Vérifie la santé du cerveau (Groq configuré)"""
        return self.groq.is_configured()
    
    def _cleanup_old_data_thread_safe(self):
        """Nettoie les anciennes données de manière thread-safe"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            
            def cleanup_operation():
                cursor = self.conn.cursor()
                cursor.execute('DELETE FROM market_features WHERE timestamp < ?', (cutoff_date,))
                cursor.execute('DELETE FROM ai_signals WHERE timestamp < ?', (cutoff_date,))
                cursor.execute('DELETE FROM model_performance WHERE timestamp < ?', (cutoff_date,))
                self.conn.commit()
                self.logger.debug("[OK] Données anciennes nettoyées (thread-safe)")
            
            self._safe_db_operation(cleanup_operation)
            
        except Exception as e:
            self.logger.error(f"[ERREUR] Erreur nettoyage données: {e}")
    
    def _retrain_model_thread_safe(self):
        """Réentraîne le modèle avec les nouvelles données (thread-safe)"""
        if self.is_training:
            return
        
        self.is_training = True
        start_time = time.time()
        
        try:
            self.logger.info("[REDEMARRAGE] Réentraînement du modèle IA...")
            
            # Simulation d'entraînement (à remplacer par vrai entraînement)
            time.sleep(2)
            
            # Sauvegarde performance (thread-safe)
            def save_performance():
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO model_performance 
                    (timestamp, model_version, accuracy, total_predictions, correct_predictions, training_duration)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now(),
                    self.model_version,
                    self.performance_metrics['accuracy'],
                    self.performance_metrics['total_predictions'],
                    self.performance_metrics['correct_predictions'],
                    time.time() - start_time
                ))
                self.conn.commit()
            
            self._safe_db_operation(save_performance)
            
            self.performance_metrics['last_training'] = datetime.now()
            self.logger.info("[OK] Modèle IA réentraîné avec succès (thread-safe)")
            
        except Exception as e:
            self.logger.error(f"[ERREUR] Erreur réentraînement modèle: {e}")
        finally:
            self.is_training = False

    def update_model_performance(self, signal: TradingSignal, profit: float, success: bool):
        """Met à jour la performance du modèle de manière thread-safe"""
        try:
            if success:
                self.performance_metrics['correct_predictions'] += 1
            
            self.performance_metrics['accuracy'] = (
                self.performance_metrics['correct_predictions'] / 
                self.performance_metrics['total_predictions']
            )
            
            # Sauvegarde en base (thread-safe)
            with db_lock:
                cursor = self.conn.cursor()
                cursor.execute('''
                    UPDATE ai_signals 
                    SET executed = TRUE, profit = ?, success = ?
                    WHERE timestamp = ? AND symbol = ?
                ''', (profit, success, signal.timestamp, signal.symbol))
                
                self.conn.commit()
            
            self.logger.info(f"[DATA] Performance modèle mise à jour: "
                           f"Accuracy: {self.performance_metrics['accuracy']:.3f}")
                           
        except Exception as e:
            self.logger.error(f"[ERREUR] Erreur mise à jour performance: {e}")
    
    def get_performance_report(self) -> Dict:
        """Génère un rapport de performance"""
        return {
            'model_version': self.model_version,
            'accuracy': round(self.performance_metrics['accuracy'], 3),
            'total_predictions': self.performance_metrics['total_predictions'],
            'correct_predictions': self.performance_metrics['correct_predictions'],
            'market_regime': self.market_regime.value,
            'last_training': self.performance_metrics['last_training'],
            'is_training': self.is_training,
            'status': 'ACTIVE'
        }

    def decide_autonomous(self, payload: Dict) -> Dict:
        """Décision autonome par IA (Groq uniquement)."""
        if not self.groq.is_configured():
            raise RuntimeError("GROQ_API_KEY manquant ou non configuré")

        context = payload.get("context", "entry")
        prompt = (
            "Tu es un moteur de trading autonome. Retourne un JSON strict. "
            "Si context='entry': action doit être BUY, SELL ou HOLD. "
            "Si action BUY/SELL, inclure entry_price, sl_price, tp_price. "
            "Si context='exit': action doit être EXIT ou HOLD. "
            "Toujours inclure confidence (0..1) et reason."
        )

        result = self.groq.chat_json(
            system=prompt,
            user=json.dumps(payload, ensure_ascii=False)
        )

        if not isinstance(result, dict):
            raise RuntimeError("Réponse Groq invalide (JSON attendu)")

        return result

# Serveur Flask pour l'AI Engine
app = Flask(__name__)
ai_engine = AdaptiveAIEngine()

@app.route('/')
def index():
    return jsonify({
        "service": "AI Engine - BTCUSD Micro Scalper V8",
        "status": "running",
        "version": "1.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "AI Engine"})

@app.route('/api/health')
def api_health():
    return jsonify({
        "status": "healthy",
        "model_version": ai_engine.model_version,
        "predictions": ai_engine.performance_metrics['total_predictions'],
        "accuracy": ai_engine.performance_metrics['accuracy']
    })

@app.route('/api/status')
def status():
    return jsonify(ai_engine.get_performance_report())

@app.route('/api/signal')
def get_signal():
    """Endpoint désactivé (IA interne supprimée)."""
    return jsonify({'error': 'endpoint disabled'}), 410

@app.route('/api/performance')
def performance():
    return jsonify(ai_engine.get_performance_report())
    
@app.route('/api/analyze', methods=['POST'])
def analyze_market_api():
    """Endpoint désactivé (IA interne supprimée)."""
    return jsonify({'error': 'endpoint disabled'}), 410

@app.route('/api/decision', methods=['POST'])
def decision_api():
    """Endpoint IA autonome pour décisions d'entrée/sortie."""
    try:
        payload = request.get_json() or {}
        decision = ai_engine.decide_autonomous(payload)
        return jsonify(decision)
    except Exception as e:
        return jsonify({'error': str(e)}), 503

def run_ai_server():
    """Démarre le serveur AI Engine"""
    print("=" * 50)
    print("[IA] MOTEUR IA ADAPTATIF - BTCUSD MICRO SCALPER V8")
    print("[WEB] Serveur: http://localhost:5003")
    print("[DATA] Port: 5003")
    print("[LOCK] Version: Thread-Safe SQLite")
    print("=" * 50)
    
    # Démarrer le moteur IA
    ai_engine.start()
    
    try:
        # Démarrer le serveur Flask
        app.run(host='0.0.0.0', port=5003, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n[ARRET] Arrêt du serveur IA...")
    except Exception as e:
        print(f"[ERREUR] Erreur: {e}")
    finally:
        ai_engine.stop()

if __name__ == "__main__":
    # Configuration logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    run_ai_server()