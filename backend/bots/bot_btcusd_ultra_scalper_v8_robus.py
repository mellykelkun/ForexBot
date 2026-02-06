# bot_btcusd_ultra_scalper_v8_robus.py
"""
BTCUSD MICRO SCALPER V8 PRO - Version Professionnelle
Avec IA adaptative, sécurité renforcée et gestion avancée
"""

import time
import math
import logging
import argparse
import numpy as np
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from collections import deque
import sqlite3
import threading
import traceback
import sys
import os
import requests
import json
import hashlib
import random

from backend.config.config_micro_scalping_pro import (
    SYMBOLS_CONFIG,
    MICRO_SCALPING_CONFIG,
    SECURITY_CONFIG,
)

LEGACY_CODE = '''

# =============== RÉSILIENCE RÉSEAU ===============
class NetworkResilienceManager:
    """Gestionnaire de résilience réseau avec reprise automatique"""
    
    def __init__(self, max_retries=3, backoff_factor=0.5):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.consecutive_failures = 0
    
    def execute_with_retry(self, operation, operation_name="", *args, **kwargs):
        """Exécute une opération avec reprise automatique"""
        for attempt in range(self.max_retries):
            try:
                result = operation(*args, **kwargs)
                self.consecutive_failures = 0
                return result
            except (requests.exceptions.ConnectionError, 
                    requests.exceptions.Timeout,
                    mt5.MT5Error,
                    Exception) as e:
                
                self.consecutive_failures += 1
                wait_time = self.backoff_factor * (2 ** attempt)
                
                logging.warning(
                    f"⚠️ Tentative {attempt + 1}/{self.max_retries} échouée pour {operation_name}. "
                    f"Attente {wait_time}s - Erreur: {str(e)[:100]}..."
                )
                time.sleep(wait_time)
        
        logging.error(f"❌ Échec après {self.max_retries} tentatives pour {operation_name}")
        return None

# =============== MÉTRIQUES AVANCÉES ===============
                return False, f"Lot trop élevé: {proposed_lot:.4f} > {max_allowed_lot:.4f}"
            
            # Vérification timing (anti-sur trading)
            if self.last_trade_time:
                time_since_last = (datetime.now() - self.last_trade_time).total_seconds()
                if time_since_last < 5:  # 5 secondes minimum entre trades
                    return False, f"Temps entre trades trop court: {time_since_last:.1f}s"
            
            return True, "Éligible"
            
        except Exception as e:
            return False, f"Erreur vérification sécurité: {e}"
    
    def record_trade_result(self, profit: float, capital: float):
        """Enregistre le résultat d'un trade pour suivi sécurité"""
                indicateurs, candle_analysis, support_resistance, tick_data
            )
            
            # 5. Décision finale basée principalement sur les chandeliers
            decision = self.prendre_decision_finale(
                indicateurs, candle_analysis, support_resistance, combined_confidence, tick_data
            )
            
            # 6. Validation du signal avec critères stricts
            if not self.valider_signal(decision, indicateurs, candle_analysis, support_resistance):
                return {'valide': False, 'raison': 'Signal non validé'}
            
            return {
                'valide': True,
                'indicateurs': indicateurs,
                'candle_analysis': candle_analysis,
                'support_resistance': support_resistance,
                'combined_confidence': combined_confidence,
                'decision': decision,
                'timestamp': datetime.now(),
                'qualite_signal': self.calculer_qualite_signal(decision, candle_analysis, support_resistance)
            }
            
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, "Analyse marché complète")
            return {'valide': False, 'raison': 'Erreur analyse'}
            
def analyser_support_resistance(self, df: pd.DataFrame) -> Dict:
    """Analyse les niveaux de support et résistance"""
    try:
        if len(df) < 20:
            return {'supports': [], 'resistances': [], 'current_position': 0.5}
        
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        # Points pivots
        pivot = (highs[-1] + lows[-1] + closes[-1]) / 3
        r1 = 2 * pivot - lows[-1]
        s1 = 2 * pivot - highs[-1]
        
        # Niveaux de support/résistance dynamiques
        resistance_levels = []
        support_levels = []
        
        # Résistances (highs récents)
        for i in range(max(0, len(highs)-10), len(highs)):
            if highs[i] == max(highs[max(0, i-5):min(len(highs), i+5)]):
                resistance_levels.append(highs[i])
        
        # Supports (lows récents)
        for i in range(max(0, len(lows)-10), len(lows)):
            if lows[i] == min(lows[max(0, i-5):min(len(lows), i+5)]):
                support_levels.append(lows[i])
        
        # Position actuelle par rapport aux niveaux
        current_price = closes[-1]
        if resistance_levels and support_levels:
            price_range = max(resistance_levels) - min(support_levels)
            if price_range > 0:
                current_position = (current_price - min(support_levels)) / price_range
            else:
                current_position = 0.5
        else:
            current_position = 0.5
        
        return {
            'supports': sorted(list(set(support_levels)))[-3:],  # 3 supports les plus proches
            'resistances': sorted(list(set(resistance_levels)))[:3],  # 3 résistances les plus proches
            'pivot': pivot,
            'r1': r1,
            's1': s1,
            'current_position': current_position
        }
        
    except Exception as e:
        logging.error(f"❌ Erreur analyse support/résistance: {e}")
        return {'supports': [], 'resistances': [], 'current_position': 0.5}

    def combiner_signaux_avances(self, indicateurs: Dict, candle_analysis: Dict, support_resistance: Dict, tick_data: Dict) -> Dict:
        """Combine intelligemment tous les signaux avec POIDS CHANDELIERS MAJORITAIRE"""
        
        
        # Renforcer la confiance si haute cohérence
        if coherence >= 0.75:  # 75% des signaux alignés
            return 1.2  # +20% de confiance
        elif coherence >= 0.5:  # 50% des signaux alignés
            return 1.0
        else:
            return 0.7  # -30% de confiance

    def prendre_decision_finale(self, indicateurs: Dict, candle_analysis: Dict, combined: Dict, tick_data: Dict) -> Dict:
        """Prend la décision finale avec gestion de risque AVANCÉE"""
        score_total = combined['score_total']
        confiance = combined['confiance_finale']
        
        # SEUIL DE CONFIANCE DYNAMIQUE
        confiance_minimale = 0.65  # Augmenté pour plus de précision
        
        if confiance < confiance_minimale:
            return {'action': 'HOLD', 'confiance': confiance, 'raison': 'Confiance insuffisante'}
        
        # DÉCISION BASÉE SUR LE SCORE TOTAL
        prix_entree = indicateurs['price']
        volatilite = tick_data.get('volatilite', 0.05) / 100.0  # Conversion en décimal
        
        # CALCUL SL/TP INTELLIGENT basé sur la volatilité et les chandeliers
        if score_total > 0.4:  # Signal haussier fort
            direction = "BUY"
            prix_sl, prix_tp, distance_stop = self.calculer_niveaux_avances(
                direction, prix_entree, volatilite, candle_analysis, 'BULLISH'
            )
            
        elif score_total > 0.2:  # Signal haussier modéré
            direction = "BUY"
            prix_sl, prix_tp, distance_stop = self.calculer_niveaux_avances(
                direction, prix_entree, volatilite, candle_analysis, 'BULLISH'
            )
            confiance *= 0.8  # Réduction confiance pour signaux modérés
            
        elif score_total < -0.4:  # Signal baissier fort
            direction = "SELL"
            prix_sl, prix_tp, distance_stop = self.calculer_niveaux_avances(
                direction, prix_entree, volatilite, candle_analysis, 'BEARISH'
            )
            
        elif score_total < -0.2:  # Signal baissier modéré
            direction = "SELL"
            prix_sl, prix_tp, distance_stop = self.calculer_niveaux_avances(
                direction, prix_entree, volatilite, candle_analysis, 'BEARISH'
            )
            confiance *= 0.8  # Réduction confiance pour signaux modérés
            
        else:
            return {'action': 'HOLD', 'confiance': confiance, 'raison': 'Signal trop faible'}
        
        # RAISON DU SIGNAL détaillée
        raison = self.generer_raison_signal(candle_analysis, indicateurs, score_total)
        
        # Calcul ratio risque/rendement
        ratio_rr = abs(prix_tp - prix_entree) / abs(prix_entree - prix_sl)
        
        return {
            'action': direction,
            'confiance': confiance,
            'prix_entree': prix_entree,
            'prix_tp': prix_tp,
            'prix_sl': prix_sl,
            'distance_stop': distance_stop,
            'ratio_risque_rendement': ratio_rr,
            'raison': raison,
            'timestamp': datetime.now().isoformat()
        }

    def calculer_niveaux_avances(self, direction: str, prix_entree: float, volatilite: float, 
                                candle_analysis: Dict, biais: str) -> Tuple[float, float, float]:
        """Calcule les niveaux SL/TP de manière intelligente"""
        
        # BASE : Stop basé sur la volatilité
        distance_stop_base = prix_entree * volatilite * 2.0
        
        # AJUSTEMENT selon la force des chandeliers
        force_chandeliers = candle_analysis.get('signal_strength', 0.5)
        
        # Stop plus serré si forts patterns de chandeliers
        if force_chandeliers > 0.7:
            multiplicateur_stop = 0.7  # -30% de stop
            multiplicateur_tp = 2.5    # +25% de TP
        elif force_chandeliers > 0.5:
            multiplicateur_stop = 0.85 # -15% de stop
            multiplicateur_tp = 2.2    # +10% de TP
        else:
            multiplicateur_stop = 1.0  # Stop normal
            multiplicateur_tp = 2.0    # TP normal
        
        distance_stop = distance_stop_base * multiplicateur_stop
        
        if direction == "BUY":
            prix_sl = prix_entree - distance_stop
            prix_tp = prix_entree + (distance_stop * multiplicateur_tp)
        else:
            prix_sl = prix_entree + distance_stop
            prix_tp = prix_entree - (distance_stop * multiplicateur_tp)
        
        return prix_sl, prix_tp, distance_stop

    def generer_raison_signal(self, candle_analysis: Dict, indicateurs: Dict, score_total: float) -> str:
        """Génère une raison détaillée du signal"""
        raisons = []
        
        # Patterns de chandeliers
            return {
                'rsi': 50,
                'macd_histogram': 0,
                'bb_position': 0.5,
                'price': 0,
                'bb_upper': 0,
                'bb_lower': 0,
                'sma': 0,
                'atr': 0.01
            }
    
    def analyser_tendance_ia(self, df: pd.DataFrame, indicateurs: Dict) -> str:
        """Analyse la tendance avec approche IA multi-critères"""
        rsi = indicateurs['rsi']
        macd_hist = indicateurs['macd_histogram']
        bb_pos = indicateurs['bb_position']
        prix_actuel = indicateurs['price']
        sma = indicateurs['sma']
        
        # Score de tendance amélioré
        score = 0
        
        # RSI > 50 = tendance haussière
        if rsi > 50: 
            score += 1
        # MACD positif = momentum haussier
        if macd_hist > 0: 
            score += 1
        # Prix au-dessus de la SMA = tendance haussière
        if prix_actuel > sma: 
            score += 1
        # Position dans les Bollinger Bands
        if bb_pos > 0.5: 
            score += 0.5
        else:
            score -= 0.5
        
        if score >= 2.5:
            return "HAUSSIERE_FORTE"
        elif score >= 1.5:
            return "HAUSSIERE"
        elif score <= 0.5:
            return "BAISSIERE_FORTE"
        elif score <= 1.0:
            return "BAISSIERE"
        else:
            return "NEUTRE"
    
    def calculer_confidence_ia(self, indicateurs: Dict, tick_data: Dict) -> float:
        """Calcule la confiance avec IA adaptative multi-facteurs"""
        confiance_base = 0.5
        
        # Facteurs de confiance RSI
        rsi = indicateurs['rsi']
        if 30 <= rsi <= 70:  # Zone neutre = plus fiable
            confiance_base += 0.2
        elif rsi < 20 or rsi > 80:  # Zones extrêmes = moins fiable
            confiance_base -= 0.2
        else:  # Zones intermédiaires
            confiance_base += 0.1
            
        # Facteur volatilité
        volatilite = tick_data.get('volatilite', 0.05)
        if 0.03 <= volatilite <= 0.08:  # Volatilité idéale
            confiance_base += 0.1
        elif volatilite > 0.15:  # Volatilité trop élevée
            confiance_base -= 0.2
        elif volatilite < 0.02:  # Volatilité trop faible
            confiance_base -= 0.1
            
        # Facteur tendance
        tendance = self.analyser_tendance_ia(pd.DataFrame(), indicateurs)
        if "FORTE" in tendance:
            confiance_base += 0.1
            
        return max(0.1, min(confiance_base, 1.0))

# =============== GESTIONNAIRE D'ERREURS AVANCÉ ===============
class GestionnaireErreursAvance:
    """Gestionnaire d'erreurs avancé avec monitoring"""
    
    def __init__(self):
        self.erreurs_recentes = deque(maxlen=20)
        self.erreurs_critiques = 0
        self.derniere_erreur = None
        self.alertes_envoyees = []
    
    def logger_erreur(self, erreur: Exception, contexte: str = "", niveau: str = "ERROR"):
        """Log une erreur avec contexte avancé"""
        message_erreur = f"❌ ERREUR {contexte}: {str(erreur)}"
        stack_trace = traceback.format_exc()
        
        if niveau == "ERROR":
            logging.error(message_erreur)
            logging.debug(f"📋 Stack trace: {stack_trace}")
            self.erreurs_critiques += 1
        elif niveau == "WARNING":
            logging.warning(message_erreur)
        
        erreur_data = {
            'timestamp': datetime.now().isoformat(),
            'contexte': contexte,
            'message': str(erreur),
            'type': type(erreur).__name__,
            'niveau': niveau,
            'stack_trace': stack_trace
        }
        self.erreurs_recentes.append(erreur_data)
        self.derniere_erreur = erreur_data
        
        # Alerte si trop d'erreurs
        if self.erreurs_critiques >= 5:
            self.envoyer_alerte_critique()
    
    def envoyer_alerte_critique(self):
        """Envoie une alerte critique"""
        if "trop_erreurs" not in self.alertes_envoyees:
            logging.critical("🚨 ALERTE CRITIQUE: Trop d'erreurs détectées!")
            self.alertes_envoyees.append("trop_erreurs")
    
    def get_statut_erreurs(self) -> Dict[str, Any]:
        """Retourne le statut complet des erreurs"""
        return {
            'erreurs_critiques': self.erreurs_critiques,
            'derniere_erreur': self.derniere_erreur,
            'total_erreurs': len(self.erreurs_recentes),
            'alertes_activees': len(self.alertes_envoyees),
            'sante_bot': 'EXCELLENTE' if self.erreurs_critiques == 0 else 
                         'MOYENNE' if self.erreurs_critiques < 3 else 'CRITIQUE'
        }

# =============== ANALYSEUR CHANDELIERS AVANCÉ ===============
class AdvancedCandlestickAnalyzer:
    """Analyseur avancé des chandeliers japonais avec détection multi-timeframe"""
    
    def __init__(self):
        self.patterns_strength = {
            # Fort retournement haussier (confiance 80-95%)
            "BULLISH_ENGULFING": 0.95,
            "MORNING_STAR": 0.90,
            "PIERCING_LINE": 0.85,
            "THREE_WHITE_SOLDIERS": 0.88,
            "HAMMER": 0.80,
            "INVERTED_HAMMER": 0.75,
            "BULLISH_KICKING": 0.85,
            
            # Fort retournement baissier (confiance 80-95%)
            "BEARISH_ENGULFING": 0.95,
            "EVENING_STAR": 0.90,
            "DARK_CLOUD_COVER": 0.85,
            "THREE_BLACK_CROWS": 0.88,
            "SHOOTING_STAR": 0.80,
            "HANGING_MAN": 0.75,
            "BEARISH_KICKING": 0.85,
            
            # Signaux moyens (confiance 60-75%)
            "BULLISH_HARAMI": 0.70,
            "BEARISH_HARAMI": 0.70,
            "BULLISH_DOJI_STAR": 0.65,
            "BEARISH_DOJI_STAR": 0.65,
            
            # Signaux faibles (confiance 40-50%)
            "DOJI": 0.40,
            "SPINNING_TOP": 0.30,
            "LONG_LEGGED_DOJI": 0.45,
            "DRAGONFLY_DOJI": 0.50,
            "GRAVESTONE_DOJI": 0.50
        }
        
        self.volume_analyzer = VolumeAnalyzer()
        
    def detect_all_patterns(self, df: pd.DataFrame) -> List[Dict]:
            total_range = high_prices[i] - low_prices[i]
            
            if total_range > 0 and body / total_range < 0.1:  # Très petit corps
                lower_wick = min(open_prices[i], close_prices[i]) - low_prices[i]
                upper_wick = high_prices[i] - max(open_prices[i], close_prices[i])
                
                # Dragonfly Doji (Haussier)
                if upper_wick == 0 and lower_wick > total_range * 0.6:
                    patterns.append({
                        'name': 'DRAGONFLY_DOJI',
                        'strength': self.patterns_strength['DRAGONFLY_DOJI'],
                        'direction': 'BULLISH',
                        'index': i,
                        'timestamp': datetime.now()
                    })
                
                # Gravestone Doji (Baissier)
                elif lower_wick == 0 and upper_wick > total_range * 0.6:
                    patterns.append({
                        'name': 'GRAVESTONE_DOJI',
                        'strength': self.patterns_strength['GRAVESTONE_DOJI'],
                        'direction': 'BEARISH',
                        'index': i,
                        'timestamp': datetime.now()
                    })
                
                # Long-Legged Doji (Neutre)
                elif lower_wick > total_range * 0.3 and upper_wick > total_range * 0.3:
                    patterns.append({
                        'name': 'LONG_LEGGED_DOJI',
                        'strength': self.patterns_strength['LONG_LEGGED_DOJI'],
                        'direction': 'NEUTRAL',
                        'index': i,
                        'timestamp': datetime.now()
                    })
                
                # Doji standard
                else:
                    patterns.append({
                        'name': 'DOJI',
                        'strength': self.patterns_strength['DOJI'],
                        'direction': 'NEUTRAL',
                        'index': i,
                        'timestamp': datetime.now()
                    })
        
        return patterns
    
    def _detect_three_patterns(self, open_prices, high_prices, low_prices, close_prices, volumes):
        """Détecte les patterns à trois bougies"""
        patterns = []
        
        for i in range(2, len(open_prices)):
            # Three White Soldiers (Haussier)
            if (close_prices[i-2] > open_prices[i-2] and
                close_prices[i-1] > open_prices[i-1] and
                close_prices[i] > open_prices[i] and
                close_prices[i-1] > close_prices[i-2] and
                close_prices[i] > close_prices[i-1] and
                open_prices[i-1] > open_prices[i-2] and
                open_prices[i] > open_prices[i-1]):
                
                patterns.append({
                    'name': 'THREE_WHITE_SOLDIERS',
                    'strength': self.patterns_strength['THREE_WHITE_SOLDIERS'],
                    'direction': 'BULLISH',
                    'index': i,
                    'timestamp': datetime.now()
                })
            
            # Three Black Crows (Baissier)
            elif (close_prices[i-2] < open_prices[i-2] and
                  close_prices[i-1] < open_prices[i-1] and
                  close_prices[i] < open_prices[i] and
                  close_prices[i-1] < close_prices[i-2] and
                  close_prices[i] < close_prices[i-1] and
                  open_prices[i-1] < open_prices[i-2] and
                  open_prices[i] < open_prices[i-1]):
                  
                patterns.append({
                    'name': 'THREE_BLACK_CROWS',
                    'strength': self.patterns_strength['THREE_BLACK_CROWS'],
                    'direction': 'BEARISH',
                    'index': i,
                    'timestamp': datetime.now()
                })
        
        return patterns
    
    def _detect_kicking_patterns(self, open_prices, close_prices):
        """Détecte les patterns de kick"""
        patterns = []
        
        for i in range(1, len(open_prices)):
            prev_body = close_prices[i-1] - open_prices[i-1]
            curr_body = close_prices[i] - open_prices[i]
            
            # Bullish Kicking
            if (prev_body < 0 and  # Bougie baissière précédente
                curr_body > 0 and  # Bougie haussière actuelle
                open_prices[i] > open_prices[i-1] and  # Gap haussier
                abs(curr_body) > abs(prev_body) * 1.2):  # Corps plus grand
                
                patterns.append({
                    'name': 'BULLISH_KICKING',
                    'strength': self.patterns_strength['BULLISH_KICKING'],
                    'direction': 'BULLISH',
                    'index': i,
                    'timestamp': datetime.now()
                })
            
            # Bearish Kicking  
            elif (prev_body > 0 and  # Bougie haussière précédente
                  curr_body < 0 and  # Bougie baissière actuelle
                  open_prices[i] < open_prices[i-1] and  # Gap baissier
                  abs(curr_body) > abs(prev_body) * 1.2):  # Corps plus grand
                  
                patterns.append({
                    'name': 'BEARISH_KICKING',
                    'strength': self.patterns_strength['BEARISH_KICKING'],
                    'direction': 'BEARISH',
                    'index': i,
                    'timestamp': datetime.now()
                })
        
        return patterns
    
    def _confirm_pattern(self, df, pattern, volumes):
        """Confirme un pattern avec analyse de volume et contexte"""
        try:
            index = pattern['index']
            if index >= len(df) or index < 0:
                return False
            
            current_candle = df.iloc[index]
            
            # CONFIRMATION PAR VOLUME
            if volumes is not None and index > 0:
                current_volume = volumes[index]
                avg_volume = np.mean(volumes[max(0, index-5):index])
                
                # Patterns forts doivent avoir volume élevé
                strong_patterns = ["ENGULFING", "MORNING_STAR", "EVENING_STAR", "THREE_WHITE_SOLDIERS", "THREE_BLACK_CROWS"]
                if any(p in pattern['name'] for p in strong_patterns):
                    if current_volume < avg_volume * 0.8:
                        return False
            
            # CONFIRMATION PAR TAILLE DE BOUGIE
            body_size = abs(current_candle['close'] - current_candle['open'])
            avg_body = abs(df['close'] - df['open']).iloc[max(0, index-10):index].mean()
            
            # Patterns doivent avoir une taille significative
            if body_size < avg_body * 0.2:
                return False
            
            # CONFIRMATION PAR POSITION DANS LA TENDANCE
            if not self._confirm_trend_context(df, pattern, index):
                return False
            
            return True
            
        except Exception as e:
            logging.debug(f"Erreur confirmation pattern: {e}")
            return False
    
    def _confirm_trend_context(self, df, pattern, index):
        """Confirme que le pattern est dans le bon contexte de tendance"""
        try:
            if index < 10:
                return True
                
            # Calcul tendance sur 10 périodes
            prices = df['close'].iloc[index-10:index]
            trend = "UP" if prices.iloc[-1] > prices.iloc[0] else "DOWN"
            
            # Patterns haussiers doivent apparaître en tendance baissière ou consolidation
            if pattern['direction'] == 'BULLISH':
                return trend != "UP"  # Meilleur en contre-tendance
            
            # Patterns baissiers doivent apparaître en tendance haussière ou consolidation  
            elif pattern['direction'] == 'BEARISH':
                return trend != "DOWN"
            
            return True
            
        except Exception as e:
            logging.debug(f"Erreur contexte tendance: {e}")
            return True
    
    def calculate_candle_strength(self, df: pd.DataFrame) -> Dict:
        """Calcule la force des chandeliers avec analyse multi-critères"""
        if len(df) < 5:
            return {'bullish_strength': 0, 'bearish_strength': 0, 'patterns': [], 'composite_score': 0}
        
        try:
            current_candle = df.iloc[-1]
            prev_candle = df.iloc[-2]
            
            # 1. DÉTECTION DES PATTERNS AVANCÉS
            patterns = self.detect_all_patterns(df)
            
            # 2. ANALYSE DE LA BOUGIE COURANTE
            body_size = abs(current_candle['close'] - current_candle['open'])
            total_range = current_candle['high'] - current_candle['low']
            body_ratio = body_size / total_range if total_range > 0 else 0
            
            upper_wick = current_candle['high'] - max(current_candle['open'], current_candle['close'])
            lower_wick = min(current_candle['open'], current_candle['close']) - current_candle['low']
            
            # 3. CALCUL DES FORCES AVEC POIDS DYNAMIQUES
            bullish_strength = 0
            bearish_strength = 0
            
            # Force des patterns (poids majoritaire)
            for pattern in patterns:
                strength = pattern['strength']
                if pattern['direction'] == 'BULLISH':
                    bullish_strength += strength * 0.8  # Poids fort pour les patterns
                else:
                    bearish_strength += strength * 0.8
            
            # Force de la forme de bougie (poids complémentaire)
            if current_candle['close'] > current_candle['open']:  # Bougie haussière
                bullish_strength += self.calculate_bullish_candle_strength(body_ratio, lower_wick, upper_wick) * 0.2
            else:  # Bougie baissière
                bearish_strength += self.calculate_bearish_candle_strength(body_ratio, upper_wick, lower_wick) * 0.2
            
            # 4. CONFIRMATION MULTI-TIMEFRAME
            if len(df) >= 20:
                mtf_confirmation = self.multi_timeframe_confirmation(df)
                bullish_strength *= mtf_confirmation['bullish_multiplier']
                bearish_strength *= mtf_confirmation['bearish_multiplier']
            
            # 5. ANALYSE DE VOLUME
            volume_analysis = self.volume_analyzer.analyze_volume(df)
            bullish_strength *= volume_analysis['bullish_multiplier']
            bearish_strength *= volume_analysis['bearish_multiplier']
            
            # Normalisation
            bullish_strength = min(1.0, bullish_strength)
            bearish_strength = min(1.0, bearish_strength)
            
            # Score composite
            composite_score = bullish_strength - bearish_strength
            
            return {
                'bullish_strength': bullish_strength,
                'bearish_strength': bearish_strength,
                'patterns': patterns,
                'composite_score': composite_score,
                'body_ratio': body_ratio,
                'wick_balance': upper_wick - lower_wick,
                'signal_strength': abs(composite_score),
                'volume_analysis': volume_analysis,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logging.error(f"❌ Erreur calcul force chandeliers: {e}")
            return {'bullish_strength': 0, 'bearish_strength': 0, 'patterns': [], 'composite_score': 0}
    
    def calculate_bullish_candle_strength(self, body_ratio: float, lower_wick: float, upper_wick: float) -> float:
        """Calcule la force d'une bougie haussière"""
        strength = 0
        
        # Forte bougie haussière (Marubozu)
        if body_ratio > 0.9:
            strength += 0.6
        elif body_ratio > 0.7:
            strength += 0.4
        elif body_ratio > 0.5:
            strength += 0.2
        
        # Marteau (longue mèche inférieure) - Fort signal haussier
        if lower_wick > upper_wick * 3 and body_ratio > 0.3:
            strength += 0.4
        
        # Bougie avec peu d'ombre supérieure - Fort momentum
        if upper_wick < lower_wick * 0.3:
            strength += 0.3
        
        return min(1.0, strength)
    
    def calculate_bearish_candle_strength(self, body_ratio: float, upper_wick: float, lower_wick: float) -> float:
        """Calcule la force d'une bougie baissière"""
        strength = 0
        
        # Forte bougie baissière (Marubozu)
        if body_ratio > 0.9:
            strength += 0.6
        elif body_ratio > 0.7:
            strength += 0.4
        elif body_ratio > 0.5:
            strength += 0.2
        
        # Étoile filante (longue mèche supérieure) - Fort signal baissier
        if upper_wick > lower_wick * 3 and body_ratio > 0.3:
            strength += 0.4
        
        # Bougie avec peu d'ombre inférieure - Fort momentum
        if lower_wick < upper_wick * 0.3:
            strength += 0.3
        
        return min(1.0, strength)
    
    def multi_timeframe_confirmation(self, df: pd.DataFrame) -> Dict:
        """Confirmation multi-timeframe pour renforcer les signaux"""
        try:
            if len(df) < 20:
                return {'bullish_multiplier': 1.0, 'bearish_multiplier': 1.0}
            
            # Analyse tendance court terme (5 périodes)
            short_trend = "UP" if df['close'].iloc[-1] > df['close'].iloc[-5] else "DOWN"
            
            # Analyse tendance moyen terme (10 périodes)
            medium_trend = "UP" if df['close'].iloc[-1] > df['close'].iloc[-10] else "DOWN"
            
            # Analyse tendance long terme (15 périodes)
            long_trend = "UP" if df['close'].iloc[-1] > df['close'].iloc[-15] else "DOWN"
            
            # Calcul multiplicateurs basé sur l'alignement des tendances
            bullish_multiplier = 1.0
            bearish_multiplier = 1.0
            
            # Renforcement si tendances alignées
            if short_trend == "UP" and medium_trend == "UP" and long_trend == "UP":
                bullish_multiplier = 1.5  # +50% de force pour signaux haussiers
            elif short_trend == "DOWN" and medium_trend == "DOWN" and long_trend == "DOWN":
                bearish_multiplier = 1.5  # +50% de force pour signaux baissiers
            
            return {
                'bullish_multiplier': bullish_multiplier,
                'bearish_multiplier': bearish_multiplier,
                'short_trend': short_trend,
                'medium_trend': medium_trend,
                'long_trend': long_trend
            }
            
        except Exception as e:
            logging.debug(f"Erreur confirmation multi-timeframe: {e}")
            return {'bullish_multiplier': 1.0, 'bearish_multiplier': 1.0}

 
        self.gestionnaire_micro = GestionnaireMicroScalpingPro(self.gestionnaire_erreurs)
        self.moteur_decision = MoteurDecisionIA(self.gestionnaire_erreurs)
        self.security_manager = SecurityManager()
        self.candle_analyzer = AdvancedCandlestickAnalyzer()
        
        #AJOUT DES 8 LIGNES
        self.data_cache = DataCache(ttl=3)
        self.structured_logger = StructuredLogger()
        self.dynamic_config = DynamicConfigManager(config_manager)
        self.network_resilience = NetworkResilienceManager()
        self.advanced_metrics = AdvancedMetrics()
        self.last_cleanup = datetime.now()
        self.config_check_interval = 60
        self.last_config_check = datetime.now()
        
        self.ai_server_thread = None
        
        self.simulation_mode = True
        
        # Statistiques avancées
        self.performance_stats = {
            'hourly_trades': deque(maxlen=24),
            'daily_profit': 0.0,
            'weekly_profit': 0.0,
            'max_drawdown': 0.0
        }
        
        self.current_market_data = {}
        self.active_trades = []        
               
    def log_activity_realtime(self, symbol: str, action: str, details: str = ""):
        """Log l'activité de trading en temps réel"""
        timestamp = datetime.now().strftime("%H:%M:%S")
    
        # Couleurs pour différents types d'actions
        action_colors = {
            "ANALYSE": "🔍",
            "SIGNAL_IA": "🤖", 
            "TRADE": "🎯",
            "EXECUTION": "⚡",
            "PROFIT": "💰",
            "PERTE": "🔴"
        }
    
        emoji = action_colors.get(action, "📝")
    
        logging.info(f"{emoji} [{timestamp}] {symbol} | {action} | {details}")
        
    def validate_spread(self, symbol, spread_pips):
        """Valide si le spread est acceptable pour le trading - VERSION AMÉLIORÉE"""
        spread_limits = {
            'BTCUSD': 70.0,    # pips max
            'EURUSD': 2.0,
            'USDJPY': 3.0,
            'GBPUSD': 2.5,
            'AUDUSD': 2.5,
            'NZDUSD': 3.0,
            'GOLD': 100.0,
            'XAUUSD': 100.0    # ✅ Ajout pour compatibilité
        }
        
        limit = spread_limits.get(symbol, 10.0)
        
        if spread_pips > limit:
            # ✅ Utilise ton système de logging existant
            self.log_activity_realtime(symbol, "SPREAD", f"Trop élevé: {spread_pips:.1f}pips > {limit}pips")
            return False
        
        # ✅ Log spread acceptable
        if spread_pips <= limit * 0.5:  # Moins de 50% de la limite
            self.log_activity_realtime(symbol, "SPREAD", f"Optimal: {spread_pips:.1f}pips")
        else:
            self.log_activity_realtime(symbol, "SPREAD", f"Acceptable: {spread_pips:.1f}pips")
        
        return True
        
    def print_trading_header(self):
        """Affiche l'en-tête du trading - VERSION SOLDE RÉEL"""
        try:
            # Vérifier statut IA en temps réel
            ia_status = "✅ CONNECTÉ" if self.check_ai_engine_connection() else "❌ DÉCONNECTÉ"
            
            # ✅ CORRECTION BALANCE - TOUJOURS LE SOLDE RÉEL
            balance_text = "N/A"
            balance_currency = "USD"
            
            try:
                # MÉTHODE PRINCIPALE: Récupération directe depuis MT5
                account_info = mt5.account_info()
                if account_info:
                    balance_text = f"${account_info.balance:.2f}"
                    balance_currency = getattr(account_info, 'currency', 'USD')
                    # Sauvegarder pour éviter de refaire l'appel
                    self.account = account_info
                    logging.info(f"✅ Balance réelle récupérée: {balance_text} {balance_currency}")
                else:
                    # MÉTHODE DE SECOURS: self.account existant
                    if hasattr(self, 'account') and self.account:
                        balance_text = f"${self.account.balance:.2f}"
                        balance_currency = getattr(self.account, 'currency', 'USD')
                        logging.info(f"✅ Balance depuis self.account: {balance_text} {balance_currency}")
                    else:
                        logging.warning("⚠️ Impossible de récupérer la balance")
                        balance_text = "EN COURS..."
                        
            except Exception as balance_error:
                                    'reason': exit_reason,
                                    'exit_score': exit_confidence,
                                    'profit': position.profit,
                                    'market_conditions': market_data
                                }
                                success = position.profit > 0
                                self.exit_guardian.record_exit_performance(symbol, exit_data, success)
                            
                            self.log_activity_realtime(symbol, "SORTIE_INTELLIGENTE", 
                                f"Fermeture IA | Profit: ${position.profit:.2f} | Confiance: {exit_confidence:.1%}")
                    
                    # Mettre à jour le monitoring (pour micro-scalping)
                    self.update_position_monitoring(position_key, position_data, market_data)
                        
        except Exception as e:
            logging.error(f"❌ Erreur surveillance positions: {e}")
                
    def get_market_analysis_for_symbol(self, symbol: str) -> Dict:
        """Analyse marché pour un symbole spécifique"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 50)
            if rates is None:
                return {}
                
            df = pd.DataFrame(rates)
            tick_data = self.get_symbol_tick_data(symbol)
            
            if not tick_data:
                return {}
                
            # Utiliser le moteur de décision existant
            analyse = self.moteur_decision.analyser_marche_complet(df, tick_data)
            
            if analyse['valide']:
                return {
                    'rsi': analyse['indicateurs']['rsi'],
                    'macd_histogram': analyse['indicateurs']['macd_histogram'],
                    'bb_position': analyse['indicateurs']['bb_position'],
                    'candle_analysis': analyse.get('candle_analysis', {}),
                    'price': analyse['indicateurs']['price']
                }
            return {}
            
        except Exception as e:
            logging.error(f"❌ Erreur analyse marché {symbol}: {e}")
            return {}

    def calculate_momentum(self, symbol: str) -> float:
        """Calcule le momentum actuel"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 10)
            if rates is None or len(rates) < 5:
                return 0.0
                
            closes = [r['close'] for r in rates]
            current_price = closes[-1]
            price_5_periods_ago = closes[-5] if len(closes) >= 5 else closes[0]
            
            momentum = (current_price - price_5_periods_ago) / price_5_periods_ago
            return momentum * 100  # Pourcentage
            
        except Exception as e:
            logging.error(f"❌ Erreur calcul momentum {symbol}: {e}")
            return 0.0

    def close_position(self, ticket: int, symbol: str) -> bool:
        """Ferme une position spécifique"""
        try:
            if self.simulation_mode:
                logging.info(f"📋 SIMULATION: Fermeture position {ticket}")
                return True
                
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return False
                
            position = position[0]
            order_type = mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": symbol,
                "volume": position.volume,
                "type": order_type,
                "price": position.price_current,
                "deviation": 20,
                "magic": MAGIC,
                "comment": "INTELLIGENT_EXIT",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            return result and result.retcode == mt5.TRADE_RETCODE_DONE
            
        except Exception as e:
            logging.error(f"❌ Erreur fermeture position {ticket}: {e}")
            return False

    def update_position_monitoring(self, position_key: str, position_data: Dict, market_data: Dict):
        """Met à jour le monitoring pour le micro-scalping"""
        try:
            if position_key not in self.active_positions_monitor:
                self.active_positions_monitor[position_key] = {
                    'open_time': datetime.now(),
                    'max_profit': position_data['profit'],
                    'profit_history': [],
                    'exit_attempts': 0
                }
            
            # Historique des profits
            monitor = self.active_positions_monitor[position_key]
            monitor['profit_history'].append(position_data['profit'])
            
            # Garder seulement les 10 derniers profits
            if len(monitor['profit_history']) > 10:
                monitor['profit_history'] = monitor['profit_history'][-10:]
                
            # Mettre à jour le profit max
            if position_data['profit'] > monitor['max_profit']:
                monitor['max_profit'] = position_data['profit']
                
            # Logique micro-scalping: sortie si profit diminue de X%
            current_profit = position_data['profit']
            if (monitor['max_profit'] > 0 and 
                current_profit < monitor['max_profit'] * 0.7):  # 30% de diminution
                logging.info(f"📉 MICRO-SCALPING: Profit en baisse, considérer sortie")
                
        except Exception as e:
            logging.error(f"❌ Erreur monitoring position: {e}")
        
    def initialize_multi_symbols(self):
        """Initialise la configuration multi-symboles"""
        try:
            self.symbols_config = SYMBOLS_CONFIG
            self.timeframes_config = TIMEFRAMES_CONFIG
            self.trading_sessions = TRADING_SESSIONS
            self.active_symbols = [] 
        
            # Symboles activés
            self.active_symbols = [symbol for symbol, config in self.symbols_config.items() 
                                  if config["enabled"]]

            # Résoudre les symboles réels MT5 (suffixes broker)
            self.symbol_map = {}
            unresolved = []
            for symbol in self.active_symbols:
                resolved = self.resolve_symbol_name(symbol)
                if resolved:
                    self.symbol_map[symbol] = resolved
                    if resolved != symbol:
                        logging.info(f"🔁 Mapping symbole: {symbol} -> {resolved}")
                else:
                    unresolved.append(symbol)

            if unresolved:
                logging.warning(f"⚠️ Symboles introuvables dans MT5: {unresolved}")
                self.active_symbols = [s for s in self.active_symbols if s not in unresolved]
        
            logging.info(f"🎯 MULTI-SYMBOLES ACTIVÉS: {len(self.active_symbols)} paires")
            for symbol in self.active_symbols:
                config = self.symbols_config[symbol]
                logging.info(f"   📊 {symbol}: Risque ×{config['risk_multiplier']}, Lot max: {config['max_lot']}")
            
            return True
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, "Initialisation multi-symboles")
            return False
                      
    def start_ai_engine_server(self):
        """Connexion à l'AI Engine existant sans démarrer de nouveau serveur"""
        try:
            # Vérifier si l'AI Engine est déjà en cours (démarré par le lanceur)
            response = requests.get('http://localhost:5003/api/health', timeout=5)
            if response.status_code == 200:
                logging.info("🌐 Connecté à l'AI Engine sur le port 5003")
                return True
            else:
                logging.warning("⚠️ AI Engine non détecté - Les signaux IA ne seront pas disponibles")
                return False
        except Exception as e:
            logging.warning(f"⚠️ AI Engine non accessible: {e}")
            return False

    def resolve_symbol_name(self, symbol: str):
        """Résout le symbole réel MT5 (suffixes broker)."""
        try:
            candidates = [symbol]

            if symbol == "GOLD":
                candidates += [
                    "XAUUSD", "XAUUSDm", "GOLDm", "XAUUSD.", "GOLD.",
                    "XAUUSDpro", "GOLDpro", "XAUUSD_r", "GOLD_r"
                ]
            elif symbol == "BTCUSD":
                candidates += [
                    "BTCUSDm", "BTCUSD.", "BTCUSDT", "BTCUSDTm",
                    "BTCUSDpro", "BTCUSD_r", "BTCUSD-ECN"
                ]
            else:
                candidates += [
                    f"{symbol}m", f"{symbol}.", f"{symbol}pro",
                    f"{symbol}_m", f"{symbol}_r", f"{symbol}-ECN"
                ]

            for name in candidates:
                info = mt5.symbol_info(name)
                if info:
                    if not info.visible:
                        mt5.symbol_select(name, True)
                    return name

            # Dernière chance: match par préfixe dans tous les symboles
            try:
                all_symbols = mt5.symbols_get()
                if all_symbols:
                    for s in all_symbols:
                        if s.name.upper().startswith(symbol.upper()):
                            info = mt5.symbol_info(s.name)
                            if info and not info.visible:
                                mt5.symbol_select(s.name, True)
                            return s.name
            except Exception:
                pass

            return None
        except Exception as e:
            logging.warning(f"⚠️ Résolution symbole échouée pour {symbol}: {e}")
            return None

    def get_current_session_symbols(self):
        """Retourne les symboles actifs pour la session actuelle - VERSION CORRIGÉE"""
        try:
            # FORCER TOUS LES SYMBOLES DISPONIBLES (test)
            all_possible_symbols = ["BTCUSD", "EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "NZDUSD", "GOLD"]
            active_symbols = []
            
            for symbol in all_possible_symbols:
                if self.is_symbol_available(symbol):
                    active_symbols.append(symbol)
                    print(f"✅ {symbol} ajouté aux symboles actifs")
        
            print(f"🎯 MULTI-SYMBOLES ACTIVÉS: {active_symbols}")
            return active_symbols
        
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, "Récupération symboles session")
            return []

            logging.info(f"🛡️ Sécurité Renforcée: Activée")
            logging.info(f"💰 Capital Minimum: ${MICRO_SCALPING_CONFIG['capital_mini']}")

            if not self.connect_mt5_secure():
                debug_symbols_availability()
                return False
            
            # Initialisation multi-symboles
            if not self.initialize_multi_symbols():
                return False    
            self.initialize_current_signals()    

            if not self.verify_multi_symbols():
                return False

            self.debug_multi_symbol_data()

            # ✅ IA interne désactivée : uniquement Groq via API externe
            try:
                response = requests.get('http://localhost:5003/api/health', timeout=2)
                if response.status_code == 200:
                    logging.info("✅ Connexion à l'AI Engine établie")
                else:
                    logging.warning("⚠️ AI Engine non disponible (Groq requis)")
            except Exception as e:
                logging.warning(f"⚠️ AI Engine non accessible: {e}")

            self.exit_guardian = None

            # Vérification éligibilité micro
            self.micro_mode_actif = self.gestionnaire_micro.verifier_eligibilite_micro(self.account.balance)

            if self.micro_mode_actif:
                logging.info("✅ MODE MICRO SCALPING MULTI-PAIRS ACTIVÉ")
            else:
                logging.warning("⚠️ MODE STANDARD (Capital insuffisant pour micro)")

            logging.info("✅ Système de caching et métriques avancées initialisé")    

            self.initial_balance = self.account.balance
            logging.info(f"💰 Solde initial: {self.initial_balance:.2f}")
            return True

        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, "Initialisation bot pro multi-pairs")
            return False                 
                      
    def verify_multi_symbols(self):
        """Vérifie la disponibilité de tous les symboles"""
        try:
         
            # ⚠️ INITIALISATION SI active_symbols EST VIDE
            if not hasattr(self, 'active_symbols') or not self.active_symbols:
                self.initialize_multi_symbols()
            unavailable_symbols = []
        
            for symbol in self.active_symbols:
                actual_symbol = self.symbol_map.get(symbol, symbol)
                si = mt5.symbol_info(actual_symbol)
                if si is None:
                    unavailable_symbols.append(symbol)
                    logging.warning(f"⚠️ Symbole {symbol} non disponible (MT5: {actual_symbol})")
                else:
                    if not si.visible:
                        mt5.symbol_select(actual_symbol, True)
                        logging.info(f"🔧 Symbole {symbol} activé (MT5: {actual_symbol})")
                
                    logging.info(f"✅ {symbol} (MT5: {actual_symbol}): Spread {si.spread} | Lot min {si.volume_min}")
        
            if unavailable_symbols:
                logging.warning(f"🚫 Symboles non disponibles: {unavailable_symbols}")
                self.active_symbols = [s for s in self.active_symbols if s not in unavailable_symbols]
        
            logging.info(f"🎯 {len(self.active_symbols)} symboles prêts au trading")
            return len(self.active_symbols) > 0
        
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, "Vérification multi-symboles")
            return False

    def debug_multi_symbol_data(self):
        """Debug des données multi-symboles"""
        try:
            print("\n" + "=" * 60)
            print("🔍 DEBUG MULTI-SYMBOLES DÉTAILLÉ")
            print("=" * 60)
        
            for symbol in self.active_symbols[:5]:  # Limiter aux 5 premiers pour éviter le spam
                actual_symbol = self.symbol_map.get(symbol, symbol)
                tick = mt5.symbol_info_tick(actual_symbol)
                if tick:
                    spread = tick.ask - tick.bid
                    symbol_config = self.symbols_config.get(symbol, {})
                
                    print(f"📊 {symbol} (MT5: {actual_symbol}):")
                    print(f"   💰 Bid: {tick.bid:.5f}, Ask: {tick.ask:.5f}")
                    print(f"   📈 Spread: {spread:.5f} points")
                    print(f"   ⚡ Multiplicateur risque: {symbol_config.get('risk_multiplier', 1.0)}")
                    print(f"   📦 Lot max: {symbol_config.get('max_lot', 0.05)}")
                    print()
        
            print("=" * 60)
        
        except Exception as e:
            print(f"❌ Erreur debug multi-symboles: {e}")

    def get_symbol_tick_data(self, symbol: str):
        """Récupère le tick data pour un symbole spécifique"""
        try:
            actual_symbol = self.symbol_map.get(symbol, symbol)
            tick = mt5.symbol_info_tick(actual_symbol)
            if tick:
                volatilite_data = self.analyser_volatilite_symbol(actual_symbol)
                spread = tick.ask - tick.bid
            
                return {
                    'symbol': symbol,
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'spread': spread,
                    'volatilite': volatilite_data['volatilite'],
                    'volatility_status': volatilite_data['statut'],
                    'timestamp': datetime.now()
                }
            return None
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, f"Récupération tick data {symbol}")
            return None

    def analyser_volatilite_symbol(self, symbol: str):
        """Analyse la volatilité pour un symbole spécifique"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1)
            if rates is None or len(rates) == 0:
                return {'volatilite': 0.0, 'statut': 'INCONNU'}
        
            bougie = rates[0]
            high = bougie['high']
            low = bougie['low']
        
            def calculer_volatilite_reelle(high: float, low: float) -> float:
                if high <= low or high <= 0:
                    return 0.0
                prix_moyen = (high + low) / 2
                range_absolu = high - low
                volatilite_pourcentage = (range_absolu / prix_moyen) * 100
                return round(volatilite_pourcentage, 3)
        
            volatilite = calculer_volatilite_reelle(high, low)
        
            # Utiliser les limites spécifiques au symbole
            symbol_limits = VOLATILITE_CONFIG["BY_SYMBOL"].get(symbol, VOLATILITE_CONFIG["GLOBAL"])
        
            if volatilite > symbol_limits.get("EXTREME", 0.15):
                statut = "EXTRÊME 🔴"
            elif volatilite > symbol_limits.get("MAX", 0.10):
                statut = "ÉLEVÉE 🟡"
            elif symbol_limits.get("MIN", 0.02) <= volatilite <= symbol_limits.get("MAX", 0.10):
                statut = "IDÉALE 🟢"
            else:
                statut = "FAIBLE ⚪"
        
            return {
                'volatilite': volatilite,
                'statut': statut,
                'range_absolu': high - low
            }
        
        except Exception as e:
            logging.error(f"❌ Erreur analyse volatilité {symbol}: {e}")
            return {'volatilite': 0.0, 'statut': 'ERREUR'}            
    
    def connect_mt5_secure(self):
        """Connexion MT5 sécurisée avec timeout"""
        try:
            if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER, timeout=10000):
                error = mt5.last_error()
                logging.error(f"❌ Échec MT5: {error}")
                return False
                
            self.account = mt5.account_info()
            if not self.account:
                logging.error("❌ Impossible infos compte")
                return False
                
            logging.info(f"🔗 MT5 connecté | Compte: {self.account.login}")
            return True
            
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, "Connexion MT5 sécurisée")
            return False

    def verify_symbol(self):
        """Vérifie la disponibilité du symbole"""
        try:
            si = mt5.symbol_info(SYMBOL)
            if si is None:
                logging.error(f"❌ Symbol {SYMBOL} non disponible")
                return False
                
            if not si.visible:
                logging.info(f"🔧 Activation du symbole {SYMBOL}...")
                mt5.symbol_select(SYMBOL, True)
                
            logging.info(f"✅ Symbol: {SYMBOL} | Spread: {si.spread} | Lot min: {si.volume_min}")
            return True
            
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, "Vérification symbol")
            return False

    def test_spread_fix(self):
        """Test la correction du spread"""
        try:
            tick_data = self.get_current_tick_data()
            if tick_data:
                spread = tick_data['spread']
                logging.info(f"🔍 TEST SPREAD CORRIGÉ:")
                logging.info(f"   📊 Valeur spread: {spread:.5f}")
                logging.info(f"   ✅ Acceptable: {self.verifier_spread_acceptable(tick_data)}")
                logging.info(f"   📈 Impact: {self.calculer_impact_spread(spread)}")
                logging.info(f"   💰 Bid: {tick_data['bid']:.2f}, Ask: {tick_data['ask']:.2f}")
            
                # Test détaillé des paliers
                impact = self.calculer_impact_spread(spread)
                logging.info(f"🎚️  Multiplicateur lot: {impact:.1%}")
            
                print("🎯" * 30)
            else:
                logging.error("❌ Impossible de récupérer les données tick")
        except Exception as e:
            logging.error(f"❌ Erreur test spread: {e}")

    def calculer_impact_spread(self, spread_actuel: float) -> float:
        """Calcule l'impact du spread sur la stratégie"""
    
        if spread_actuel <= 20.0:    # ≤ 20 points
            logging.info(f"✅ Spread optimal: {spread_actuel:.5f} points")
            return 1.0   # Trading normal
        elif spread_actuel <= 50.0:  # 20-50 points  
            logging.warning(f"⚠️ Spread acceptable: {spread_actuel:.5f} points - Réduction 20%")
            return 0.8   # Réduction 20%
        elif spread_actuel <= 80.0:  # 50-80 points
            logging.warning(f"🚨 Spread élevé: {spread_actuel:.5f} points - Réduction 40%")
            return 0.6   # Réduction 40%
        elif spread_actuel <= 100.0:  # 80-100 points
            logging.warning(f"🔥 Spread critique: {spread_actuel:.5f} points - Réduction 50%")
            return 0.5   # Réduction 50% - TRÈS LIMITÉ
        else:
            logging.error(f"❌ Spread bloquant: {spread_actuel:.5f} points - AUCUN TRADE")
            return 0.0   # AUCUN TRADE
            
    def confirmer_correction_spread(self):
        """Confirme que la correction spread fonctionne"""
        tick_data = self.get_current_tick_data()
        if tick_data:
            spread = tick_data['spread']
            acceptable = self.verifier_spread_acceptable(tick_data)
            impact = self.calculer_impact_spread(spread)
        
            print("\n" + "🎉" * 2)
            print("🎉 CORRECTION SPREAD CONFIRMÉE")
            print("🎉" * 2)
            print(f"📊 Spread actuel: {spread:.1f} points")
            print(f"✅ Trading autorisé: {acceptable}")
            print(f"📈 Impact sur lots: {impact:.0%}")
            print(f"💡 Statut: Spread ÉLEVÉ - Trading réduit à 60%")
            print("🎉" * 2)
            
            
    def debug_spread_data(self):
        """Debug détaillé des données de spread - VERSION CORRIGÉE"""
        try:
            tick = mt5.symbol_info_tick(SYMBOL)
            if tick:
                spread_correct = tick.ask - tick.bid
                spread_points = spread_correct
        
                print("\n" + "=" * 60)
                print("🔍 DEBUG SPREAD DÉTAILLÉ - CORRIGÉ")
                print("=" * 60)
                print(f"💰 Bid: {tick.bid:.5f}")
                print(f"💰 Ask: {tick.ask:.5f}")
                print(f"📊 Spread calculé: {spread_points:.5f} points")
                print(f"📊 Spread en pips: {spread_points / 10:.1f} pips")
                print(f"📉 Spread en %: {(spread_points / tick.bid) * 100:.4f}%")
            
                # ✅ Récupération sécurisée du volume et time
                volume = getattr(tick, 'volume', 'N/A')
                time_str = getattr(tick, 'time', 'N/A')
                print(f"📈 Volume: {volume}")
                print(f"🕒 Time: {time_str}")
                print("=" * 60)
        
                # ✅ TEST AVEC SEUILS RÉELS POUR BTC (en points réels)
                seuils = [20.0, 50.0, 80.0, 100.0]  # Points réels, pas décimales
                print("🎯 TEST SEUILS SPREAD (points réels):")
                for seuil in seuils:
                    statut = "✅ OK" if spread_points <= seuil else "❌ DÉPASSÉ"
                    pourcentage = (spread_points / seuil) * 100
                    print(f"   Seuil {seuil:5.1f} points: {statut} ({pourcentage:.1f}% du seuil)")
        
                print("=" * 60)
        
        except Exception as e:
            print(f"❌ Erreur debug spread: {e}")
            import traceback
            traceback.print_exc()       

    def verifier_spread_acceptable(self, tick_data: Dict) -> bool:
        """Vérifie si le spread permet le trading"""
        if not tick_data:
            return False
    
        spread_actuel = tick_data['spread']
    
               # ✅✅✅ SEUILS CORRIGÉS POUR BTC/USD (EN POINTS RÉELS)
        if spread_actuel > 100.0:  # 100 points MAX = 10 pips
            logging.warning(f"🛑 SPREAD TROP ÉLEVÉ: {spread_actuel:.2f} points > 100.0 points max")
            return False
        elif spread_actuel > 50.0:  # 50-100 points - Élevé
            logging.warning(f"⚠️ Spread élevé: {spread_actuel:.2f} points - Réduction agressivité")
            return True
        elif spread_actuel > 20.0:  # 20-50 points - Normal
            logging.info(f"✅ Spread normal: {spread_actuel:.2f} points")
            return True
        else:  # < 20 points - Optimal
            logging.info(f"🎯 Spread optimal: {spread_actuel:.2f} points")
            return True
   
    def verify_connection(self):
        """Vérifie et maintient la connexion MT5"""
        try:
            if not mt5.initialize() or self.gestionnaire_erreurs.erreurs_critiques >= 3:
                logging.warning("🔄 Tentative de reconnexion MT5...")
                return self.connect_mt5_secure()
            return True
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, "Vérification connexion")
            return self.connect_mt5_secure()

    def get_active_trades(self):
        """Récupère les trades actifs"""
        try:
            positions = mt5.positions_get(symbol=SYMBOL)
            if positions:
                return [{
                    'ticket': pos.ticket,
                    'direction': 'BUY' if pos.type == 0 else 'SELL',
                    'entry_price': pos.price_open,
                    'profit': pos.profit,
                    'volume': pos.volume,
                    'current_price': pos.price_current,
                    'sl': pos.sl,
                    'tp': pos.tp,
                    'status': 'OPEN'
                } for pos in positions]
            return []
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, "Récupération trades actifs")
            return []

    def get_current_tick_data(self):
        """Récupère le tick actuel"""
        try:
            tick = mt5.symbol_info_tick(SYMBOL)
            if tick:
                volatilite_data = analyser_volatilite_courante(SYMBOL)
                
                # ✅ CALCUL CORRIGÉ DU SPREAD
                spread_correct = tick.ask - tick.bid
                return {
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'spread': spread_correct,
                    'volatilite': volatilite_data['volatilite'],
                    'volatility_status': volatilite_data['statut'],
                    'timestamp': datetime.now()
                }
            return None
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, "Récupération tick data")
            return None

    def get_market_analysis(self):
        """Analyse complète du marché"""
        try:
            rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 50)
            if rates is None:
                return None
                
            df = pd.DataFrame(rates)
            tick_data = self.get_current_tick_data()
            
            if tick_data is None:
                return None
            
            analyse = self.moteur_decision.analyser_marche_complet(df, tick_data)
            
            if analyse['valide']:
                return {
                    'rsi': analyse['indicateurs']['rsi'],
                    'macd_histogram': analyse['indicateurs']['macd_histogram'],
                    'bb_position': analyse['indicateurs']['bb_position'],
                    'trend': analyse['tendance'],
                    'confidence': analyse['confidence_ia'],
                    'price': analyse['indicateurs']['price'],
                    'bb_upper': analyse['indicateurs']['bb_upper'],
                    'bb_lower': analyse['indicateurs']['bb_lower'],
                    'sma': analyse['indicateurs']['sma']
                }
            return None
            
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, "Analyse marché")
            return None   
    
    def executer_strategie_micro_ia(self):
        """Exécute la stratégie micro avec IA pour tous les symboles actifs"""
        try:
            # Récupérer les symboles de la session actuelle
            current_symbols = self.get_current_session_symbols()
            print(f"🔍 DEBUG: Symboles actifs: {current_symbols}") 
            if not current_symbols:
                print("🔍 DEBUG: Aucun symbole actif") 
                return None
        
            best_signal = None
            highest_confidence = 0
        
            # Analyser chaque symbole
            for symbol in current_symbols:
                signal = self.analyser_symbol(symbol)
                if signal and signal['confidence'] > highest_confidence:
                    highest_confidence = signal['confidence']
                    best_signal = signal
        
            return best_signal
        
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, "Stratégie multi-symboles")
            return None

    def analyser_symbol(self, symbol: str):
        """Analyse un symbole spécifique pour signal de trading"""
        try:
            # Log de début d'analyse
            self.log_activity_realtime(symbol, "ANALYSE", "Début analyse marché")
            
            # Vérifier les trades actifs pour ce symbole
            active_trades = self.get_active_trades_for_symbol(symbol)
            if active_trades:
                self.log_activity_realtime(symbol, "ANALYSE", f"Trade actif détecté - skip")
                return None
            
            # Récupérer données
            tick_data = self.get_symbol_tick_data(symbol)
            if not tick_data:
                self.log_activity_realtime(symbol, "ANALYSE", "Données tick non disponibles")
                return None
                
            # Récupération données historiques
            rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, 50)
            if rates is None:
                self.log_activity_realtime(symbol, "ANALYSE", "Données historiques non disponibles")
                return None
                
            df = pd.DataFrame(rates)

            indicateurs = self.moteur_decision.calculer_indicateurs_avances(df)
            candle_analysis = self.candle_analyzer.calculate_candle_strength(df)

            # ✅ Le bot fournit les infos, l'IA décide
            market_payload = {
                'symbol': symbol,
                'bid': tick_data['bid'],
                'ask': tick_data['ask'],
                'spread': tick_data['spread'],
                'volatility': tick_data.get('volatilite', 0.05) / 100.0,
                'volume': tick_data.get('volume', 1000),
                'indicators': indicateurs,
                'candle_analysis': candle_analysis
            }

            ai_decision = self.get_ai_decision({
                'context': 'entry',
                'symbol': symbol,
                'market_data': market_payload,
                'positions': [],
                'recent_signals': self.current_signals.get(symbol, {})
            })

            if not ai_decision:
                self.current_signals[symbol] = {
                    'direction': 'HOLD',
                    'confidence': 0,
                    'ia_confidence': 0,
                    'timestamp': datetime.now().isoformat()
                }
                return None

            action = ai_decision.get('action', 'HOLD').upper()
            confidence = float(ai_decision.get('confidence', 0))

            if action == 'HOLD':
                self.current_signals[symbol] = {
                    'direction': 'HOLD',
                    'confidence': 0,
                    'ia_confidence': confidence,
                    'timestamp': datetime.now().isoformat()
                }
                self.log_activity_realtime(symbol, "SIGNAL_IA", f"HOLD | Confiance: {confidence:.1%}")
                return None

            entry_price = ai_decision.get('entry_price') or tick_data.get('ask') or tick_data.get('bid')
            sl_price = ai_decision.get('sl_price')
            tp_price = ai_decision.get('tp_price')

            if not entry_price or sl_price is None or tp_price is None:
                self.log_activity_realtime(symbol, "SIGNAL_IA", "Décision IA incomplète (prix/SL/TP manquants)")
                return None

            stop_distance = abs(entry_price - sl_price)
            lot = self.calculate_multi_symbol_lot(
                symbol,
                self.account.balance,
                stop_distance,
                tick_data.get('volatilite', 0.05)
            )

            if lot <= 0:
                self.log_activity_realtime(symbol, "SIGNAL_IA", "Lot calculé invalide")
                return None

            signal = {
                'symbol': symbol,
                'direction': action,
                'lot': lot,
                'entry_price': entry_price,
                'sl_price': sl_price,
                'tp_price': tp_price,
                'confidence': confidence,
                'ia_confidence': confidence,
                'volatilite': tick_data.get('volatilite', 0),
                'rsi': indicateurs.get('rsi', 50),
                'micro_mode': True,
                'ia_decision': True,
                'ai_engine_signal': True,
                'regime': ai_decision.get('regime', 'RANGING'),
                'timestamp': datetime.now().isoformat()
            }

            self.log_activity_realtime(symbol, "TRADE", 
                f"PRÊT | {action} | Lot: {lot:.4f} | TP: {tp_price:.2f} | SL: {sl_price:.2f}")

            self.current_signals[symbol] = {
                'direction': signal['direction'],
                'confidence': signal['confidence'],
                'ia_confidence': signal.get('ia_confidence', signal['confidence']),
                'timestamp': datetime.now().isoformat()
            }

            return signal
            
        except Exception as e:
            self.log_activity_realtime(symbol, "ANALYSE", f"ERREUR: {str(e)}")
            return None

    def get_ai_decision(self, payload: Dict) -> Optional[Dict]:
        """Récupère une décision autonome IA (entrée/sortie) via API REST"""
        try:
            response = requests.post(
                'http://localhost:5003/api/decision',
                json=payload,
                timeout=4
            )
            if response.status_code == 200:
                return response.json()
            logging.warning(f"⚠️ Décision IA non reçue: {response.status_code}")
            return None
        except Exception as e:
            logging.error(f"❌ Erreur récupération décision IA: {e}")
            return None
            
    def calculate_trend_improved(self, df: pd.DataFrame, current_price: float) -> str:
        """Calcule le trend de manière plus robuste avec analyse multi-périodes"""
        try:
            if len(df) < 20:  # ✅ PLUS DE DONNÉES POUR PLUS DE FIABILITÉ
                return "NEUTRAL"
            
            # ✅ ANALYSE MULTI-TIMEFRAME POUR CONFIRMATION
            # Court terme (5 périodes)
            short_ma = df['close'].iloc[-5:].mean()
            
            # Moyen terme (10 périodes) 
            medium_ma = df['close'].iloc[-10:].mean()
            
            # Long terme (15 périodes)
            long_ma = df['close'].iloc[-15:].mean()
            
            # ✅ CALCUL DES PENTES RELATIVES
            short_vs_medium = ((short_ma - medium_ma) / medium_ma) * 100
            medium_vs_long = ((medium_ma - long_ma) / long_ma) * 100
            short_vs_long = ((short_ma - long_ma) / long_ma) * 100
            
            # ✅ ANALYSE DES HIGHS/LOWS RÉCENTS
            recent_highs = df['high'].iloc[-5:].max()
            recent_lows = df['low'].iloc[-5:].min()
            previous_highs = df['high'].iloc[-10:-5].max()
            previous_lows = df['low'].iloc[-10:-5].min()
            
            # ✅ CRITÈRES DE CONFIRMATION STRICTS
            bullish_conditions = 0
            bearish_conditions = 0
            
            # Condition 1: Alignement des moyennes
            if short_ma > medium_ma > long_ma:
                bullish_conditions += 1
            elif short_ma < medium_ma < long_ma:
                bearish_conditions += 1
            
            # Condition 2: Force du mouvement
            if short_vs_medium > 0.02 and medium_vs_long > 0.01:  # ✅ SEUILS AUGMENTÉS
                bullish_conditions += 1
            elif short_vs_medium < -0.02 and medium_vs_long < -0.01:
                bearish_conditions += 1
            
            # Condition 3: Nouveaux highs/lows
            if recent_highs > previous_highs:
                bullish_conditions += 1
            if recent_lows < previous_lows:
                bearish_conditions += 1
            
            # Condition 4: Position par rapport aux moyennes
            if current_price > medium_ma > long_ma:
                bullish_conditions += 1
            elif current_price < medium_ma < long_ma:
                bearish_conditions += 1
            
            # ✅ DÉCISION BASÉE SUR LE NOMBRE DE CONFIRMATIONS
            if bullish_conditions >= 3:  # ✅ AU MOINS 3 CONFIRMATIONS
                return "UP"
            elif bearish_conditions >= 3:
                return "DOWN"
            else:
                return "NEUTRAL"
                
        except Exception as e:
            logging.error(f"❌ Erreur calcul trend: {e}")
            return "NEUTRAL"
            
    def analyser_support_resistance(self, df: pd.DataFrame) -> Dict:
        """Analyse PRÉCISE des supports/résistances pour une meilleure précision des signaux"""
        try:
            if len(df) < 25:  # ✅ PLUS DE DONNÉES POUR PLUS DE PRÉCISION
                return {'supports': [], 'resistances': [], 'current_position': 0.5, 'strength': 0}
            
            highs = df['high'].values
            lows = df['low'].values
            closes = df['close'].values
            current_price = closes[-1]
            
            # ✅ POINTS PIVOTS AVANCÉS
            pivot = (highs[-1] + lows[-1] + closes[-1]) / 3
            r1 = 2 * pivot - lows[-1]
            s1 = 2 * pivot - highs[-1]
            r2 = pivot + (highs[-1] - lows[-1])
            s2 = pivot - (highs[-1] - lows[-1])
            
            # ✅ DÉTECTION DES NIVEAUX DYNAMIQUES AVEC CONFIRMATION
            resistance_levels = []
            support_levels = []
            
            # Analyse sur 20 périodes pour plus de fiabilité
            for i in range(max(0, len(highs)-20), len(highs)):
                if i >= 3 and i < len(highs)-3:
                    # ✅ RÉSISTANCES : Highs significatifs avec confirmation
                    if highs[i] == max(highs[i-3:i+3]) and highs[i] > np.mean(highs[i-5:i+1]) * 1.005:
                        # Vérifier le volume (si disponible) pour confirmation
                        resistance_levels.append({
                            'price': highs[i],
                            'strength': min(1.0, (highs[i] - np.mean(highs[i-3:i])) / np.mean(highs[i-3:i]) * 100),
                            'touches': 1
                        })
                    
                    # ✅ SUPPORTS : Lows significatifs avec confirmation  
                    if lows[i] == min(lows[i-3:i+3]) and lows[i] < np.mean(lows[i-5:i+1]) * 0.995:
                        support_levels.append({
                            'price': lows[i],
                            'strength': min(1.0, (np.mean(lows[i-3:i]) - lows[i]) / np.mean(lows[i-3:i]) * 100),
                            'touches': 1
                        })
            
            # ✅ FILTRAGE ET CLASSEMENT DES NIVEAUX
            # Regrouper les niveaux proches (±0.1%)
            def group_levels(levels, threshold_percent=0.001):
                if not levels:
                    return []
                levels_sorted = sorted(levels, key=lambda x: x['price'])
                grouped = []
                current_group = [levels_sorted[0]]
                
                for level in levels_sorted[1:]:
                    if abs(level['price'] - current_group[0]['price']) / current_group[0]['price'] <= threshold_percent:
                        current_group.append(level)
                    else:
                        # Calculer la moyenne pondérée du groupe
                        avg_price = np.mean([l['price'] for l in current_group])
                        total_strength = sum([l['strength'] for l in current_group])
                        total_touches = sum([l.get('touches', 1) for l in current_group])
                        grouped.append({
                            'price': avg_price,
                            'strength': total_strength / len(current_group),
                            'touches': total_touches
                        })
                        current_group = [level]
                
                # Ajouter le dernier groupe
                if current_group:
                    avg_price = np.mean([l['price'] for l in current_group])
                    total_strength = sum([l['strength'] for l in current_group])
                    total_touches = sum([l.get('touches', 1) for l in current_group])
                    grouped.append({
                        'price': avg_price,
                        'strength': total_strength / len(current_group),
                        'touches': total_touches
                    })
                
                return sorted(grouped, key=lambda x: x['price'])
            
            resistance_levels = group_levels(resistance_levels)
            support_levels = group_levels(support_levels)
            
            # ✅ GARDER LES MEILLEURS NIVEAUX (force + proximité)
            def filter_best_levels(levels, current_price, is_resistance=True, max_levels=3):
                if not levels:
                    return []
                # Calculer un score combiné (force + proximité)
                for level in levels:
                    distance = abs(level['price'] - current_price) / current_price
                    proximity_score = max(0, 1 - distance * 10)  # Plus proche = meilleur score
                    level['score'] = level['strength'] * 0.6 + level.get('touches', 1) * 0.2 + proximity_score * 0.2
                
                # Filtrer et trier
                if is_resistance:
                    levels = [l for l in levels if l['price'] > current_price]
                else:
                    levels = [l for l in levels if l['price'] < current_price]
                
                return sorted(levels, key=lambda x: x['score'], reverse=True)[:max_levels]
            
            best_resistances = filter_best_levels(resistance_levels, current_price, is_resistance=True)
            best_supports = filter_best_levels(support_levels, current_price, is_resistance=False)
            
            # ✅ CALCUL DE LA POSITION ACTUELLE AVEC PRÉCISION
            current_position = 0.5
            zone_strength = 0
            
            if best_supports and best_resistances:
                nearest_support = max([s['price'] for s in best_supports])
                nearest_resistance = min([r['price'] for r in best_resistances])
                
                if nearest_resistance > nearest_support:
                    price_range = nearest_resistance - nearest_support
                    current_position = (current_price - nearest_support) / price_range
                    
                    # Calcul de la force de la zone actuelle
                    support_strength = max([s['strength'] for s in best_supports]) if best_supports else 0
                    resistance_strength = max([r['strength'] for r in best_resistances]) if best_resistances else 0
                    zone_strength = (support_strength + resistance_strength) / 2
            
            # ✅ DÉTECTION DE LA ZONE DE PRIX
            zone = "NEUTRE"
            if current_position < 0.3:
                zone = "PRÈS SUPPORT"
            elif current_position > 0.7:
                zone = "PRÈS RÉSISTANCE"
            elif 0.4 <= current_position <= 0.6:
                zone = "ZONE CENTRALE"
            
            return {
                'supports': [s['price'] for s in best_supports],
                'resistances': [r['price'] for r in best_resistances],
                'support_strengths': [s['strength'] for s in best_supports],
                'resistance_strengths': [r['strength'] for r in best_resistances],
                'pivot': pivot,
                'r1': r1, 'r2': r2,
                's1': s1, 's2': s2,
                'current_position': current_position,
                'zone': zone,
                'zone_strength': zone_strength,
                'nearest_support': best_supports[0]['price'] if best_supports else current_price * 0.98,
                'nearest_resistance': best_resistances[0]['price'] if best_resistances else current_price * 1.02,
                'distance_to_support': (current_price - (best_supports[0]['price'] if best_supports else current_price)) / current_price * 100,
                'distance_to_resistance': ((best_resistances[0]['price'] if best_resistances else current_price) - current_price) / current_price * 100
            }
            
        except Exception as e:
            logging.error(f"❌ Erreur analyse support/résistance: {e}")
            return {
                'supports': [], 
                'resistances': [], 
                'current_position': 0.5, 
                'zone': 'ERREUR',
                'zone_strength': 0
            }
            
    def debug_rsi_logic(self, symbol: str, rsi: float, trend: str):
        """Debug de la logique RSI"""
        print(f"\n🧪 DEBUG LOGIQUE RSI - {symbol}")
        print(f"📊 RSI: {rsi:.1f}")
        print(f"📈 Trend: {trend}")
        
        # Test des différentes conditions
        conditions = [
            (rsi > 75, "RSI > 75 → VENTE FORTE"),
            (rsi > 65 and trend == "UP", "RSI > 65 + Trend UP → VENTE"),
            (rsi < 25, "RSI < 25 → ACHAT FORT"),
            (rsi < 35 and trend == "DOWN", "RSI < 35 + Trend DOWN → ACHAT"),
            (40 <= rsi <= 60, "RSI 40-60 → ZONE NEUTRE"),
            (60 < rsi <= 65, "RSI 60-65 → ZONE HAUTE"),
            (35 <= rsi < 40, "RSI 35-40 → ZONE BASSE")
        ]
        
        for condition, description in conditions:
            status = "✅" if condition else "❌"
            print(f"   {status} {description}")

    def get_active_trades_for_symbol(self, symbol: str):
        """Récupère les trades actifs pour un symbole spécifique"""
        try:
            positions = mt5.positions_get(symbol=symbol)
            return positions if positions else []
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, f"Récupération trades {symbol}")
            return []

    def verifier_spread_acceptable_multi(self, symbol: str, tick_data: Dict) -> bool:
        if not tick_data:
            return False

        spread_actuel = tick_data['spread']
        
        # LIMITES SPÉCIFIQUES PAR SYMBOLE (EN POINTS)
        spread_limits = {
            'BTCUSD': 80.0,      # 80 pips max pour BTCUSD
            'GOLD': 200.0,       # 200 pips max pour GOLD (or)
            'XAUUSD': 200.0,     # 200 pips max pour XAUUSD
            'EURUSD': 5.0,       # 0.5 pips
            'USDJPY': 5.0,       # 0.5 pips  
            'GBPUSD': 5.0,       # 0.5 pips
            'AUDUSD': 5.0,       # 0.5 pips
            'NZDUSD': 5.0,       # 0.5 pips
            'USDZAR': 50.0       # 5 pips
        }
            
        max_spread = spread_limits.get(symbol, 20.0)  # Default 20 points
        
        if spread_actuel > max_spread:
            logging.warning(f"🛑 {symbol} SPREAD TROP ÉLEVÉ: {spread_actuel:.2f} > {max_spread:.2f}")
            return False
        
        logging.info(f"✅ {symbol} Spread acceptable: {spread_actuel:.2f} points")
        return True
        
    def debug_gold_spread(self):
        """Debug spécifique pour le spread de GOLD"""
        try:
            symbol = "GOLD"
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                spread_points = tick.ask - tick.bid
                symbol_info = mt5.symbol_info(symbol)
                
                print(f"\n🔍 DEBUG SPREAD GOLD:")
                print(f"💰 Bid: {tick.bid:.2f}")
                print(f"💰 Ask: {tick.ask:.2f}")
                print(f"📊 Spread points: {spread_points:.2f}")
                print(f"📊 Spread pips: {spread_points:.1f} pips")  # GOLD: 1 point = 1 pip
                print(f"🎯 Digits: {symbol_info.digits}")
                print(f"📈 Tick size: {symbol_info.trade_tick_size}")
                print(f"💎 Tick value: {symbol_info.trade_tick_value}")
                
                # Vérification avec différentes méthodes
                spread_method1 = spread_points  # Méthode directe
                print(f"🧮 Calcul spread - Méthode directe: {spread_method1:.1f} pips")
                
            else:
                print(f"❌ Pas de données tick pour GOLD")
                
        except Exception as e:
            print(f"💥 Erreur debug GOLD: {e}")

    def prendre_decision_ia_multi(self, symbol: str, analyse: Dict, tick_data: Dict) -> Optional[Dict]:
        """Prend la décision finale avec IA pour un symbole spécifique"""
        try:
            if not self.verifier_spread_acceptable_multi(symbol, tick_data):
                return None

            indicateurs = analyse['indicateurs']
            confidence_ia = analyse['confidence_ia']
        
            # Seuil de confiance adaptatif
            confidence_threshold = MICRO_SCALPING_CONFIG['required_confidence']
            if confidence_ia > 0.8:
                confidence_threshold *= 0.9
        
            if confidence_ia < confidence_threshold:
                return None
        
            # Décision basée sur indicateurs (même logique que précédemment)
            rsi = indicateurs['rsi']
            macd_hist = indicateurs['macd_histogram']
            bb_pos = indicateurs['bb_position']
        
            if rsi < 30 and macd_hist > 0 and bb_pos < 0.2:
                direction = "BUY"
            elif rsi > 70 and macd_hist < 0 and bb_pos > 0.8:
                direction = "SELL"
            else:
                return None
        
            # Calcul niveaux avec IA
            entry_price = tick_data['ask'] if direction == "BUY" else tick_data['bid']
            stop_distance = entry_price * 0.001  # 0.1% stop distance
        
            if direction == "BUY":
                sl_price = entry_price - stop_distance
                tp_price = entry_price + (stop_distance * 1.5)
            else:
                sl_price = entry_price + stop_distance
                tp_price = entry_price - (stop_distance * 1.5)
        
            return {
                'direction': direction,
                'entry_price': entry_price,
                'sl_price': sl_price,
                'tp_price': tp_price,
                'confidence': confidence_ia,
                'ia_confidence': confidence_ia,
                'stop_distance': stop_distance
            }
        
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, f"Prise décision IA {symbol}")
            return None    
    
    def prendre_decision_ia(self, analyse: Dict, tick_data: Dict) -> Optional[Dict]:
        """Prend la décision finale avec IA"""
        try:
            spread_actuel = tick_data['spread']
            if spread_actuel > 0.00100:
                return None

            indicateurs = analyse['indicateurs']
            confidence_ia = analyse['confidence_ia']
            
            # Seuil de confiance adaptatif
            confidence_threshold = MICRO_SCALPING_CONFIG['required_confidence']
            if confidence_ia > 0.8:
                confidence_threshold *= 0.9  # Réduction seuil si haute confiance IA
            
            if confidence_ia < confidence_threshold:
                return None
            
            # Décision basée sur indicateurs
            rsi = indicateurs['rsi']
            macd_hist = indicateurs['macd_histogram']
            bb_pos = indicateurs['bb_position']
            
            # Logique de décision améliorée
            if rsi < 30 and macd_hist > 0 and bb_pos < 0.2:
                direction = "BUY"
            elif rsi > 70 and macd_hist < 0 and bb_pos > 0.8:
                direction = "SELL"
            else:
                return None
            
            # Calcul niveaux avec IA
            entry_price = tick_data['ask'] if direction == "BUY" else tick_data['bid']
            stop_distance = entry_price * 0.001  # 0.1% stop distance
            
            if direction == "BUY":
                sl_price = entry_price - stop_distance
                tp_price = entry_price + (stop_distance * 1.5)
            else:
                sl_price = entry_price + stop_distance
                tp_price = entry_price - (stop_distance * 1.5)
            
            return {
                'direction': direction,
                'entry_price': entry_price,
                'sl_price': sl_price,
                'tp_price': tp_price,
                'confidence': confidence_ia,
                'ia_confidence': confidence_ia,
                'stop_distance': stop_distance
            }
            
        except Exception as e:
            self.gestionnaire_erreurs.logger_erreur(e, "Prise décision IA")
            return None

    def executer_trade(self, signal):
        """Exécute le trade avec logging détaillé"""
        symbol = signal['symbol']
        
        # Log de début d'exécution
        self.log_activity_realtime(symbol, "EXECUTION", 
            f"Tentative | {signal['direction']} | Lot: {signal['lot']:.4f}")
        
        if self.simulation_mode:
            self.log_activity_realtime(symbol, "EXECUTION", "SIMULATION - Trade exécuté")
            self.gestionnaire_micro.enregistrer_trade()
            return True
            
        try:
            # Envoyer ordre MT5
            order_type = mt5.ORDER_TYPE_BUY if signal['direction'] == "BUY" else mt5.ORDER_TYPE_SELL
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": signal['lot'],
                "type": order_type,
                "price": signal['entry_price'],
                "sl": signal['sl_price'],
                "tp": signal['tp_price'],
                "deviation": 20,
                "magic": MAGIC,
                "comment": f"MICRO_V8_IA_{signal['direction']}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.trade_count += 1
                self.gestionnaire_micro.enregistrer_trade()
                
                # Log de succès
                self.log_activity_realtime(symbol, "EXECUTION", 
                    f"SUCCÈS | Ticket: {result.order} | Prix: {signal['entry_price']:.2f}")
                
                return True
            else:
                error_msg = mt5.last_error()
                self.log_activity_realtime(symbol, "EXECUTION", f"ÉCHEC: {error_msg}")
                return False
                
        except Exception as e:
            self.log_activity_realtime(symbol, "EXECUTION", f"ERREUR: {str(e)}")
            return False

    def initialize_current_signals(self):
        """Initialise les données de signaux pour tous les symboles"""
        self.current_signals = {}
        for symbol in self.active_symbols:
            self.current_signals[symbol] = {
                'direction': 'HOLD',
                'confidence': 0.0,
                'ia_confidence': 0.0,
                'timestamp': datetime.now().isoformat()
            }        


    def perform_health_check(self):
        """Vérification santé du système - VERSION CORRIGÉE"""
        try:
            # Vérification connexion MT5 - APPROCHE CORRIGÉE
            mt5_healthy = self.verify_mt5_health()
            if not mt5_healthy:
                logging.error("🔴 Santé: Connexion MT5 perdue")
                return False
            
            # Vérification compte - APPROCHE SÉCURISÉE
            if not hasattr(self, 'account') or not self.account:
                # Tentative de récupération
                self.account = mt5.account_info()
                if not self.account:
                    logging.error("🔴 Santé: Compte MT5 temporairement indisponible")
                    return False
            
            # Vérification sécurité
            security_status = self.security_manager.get_security_status()
            if security_status['status'] == 'WARNING':
                logging.warning(f"🟡 Santé: Alertes sécurité - {security_status['consecutive_losses']} pertes consécutives")
            
            # Vérification symboles
            symbol_ok = True
            for symbol in self.active_symbols[:3]:  # Vérifier seulement 3 symboles
                if not mt5.symbol_info(symbol):
                    logging.warning(f"🟡 Santé: Symbole {symbol} temporairement indisponible")
                    symbol_ok = False
                    break
            
            if not symbol_ok:
                logging.warning("🟡 Santé: Certains symboles temporairement indisponibles")
                # Ne pas retourner False pour ça - c'est temporaire
            
            logging.info("🟢 Santé: Système opérationnel")
            return True
            
        except Exception as e:
            logging.error(f"🔴 Santé: Erreur vérification - {e}")
            # Tentative de récupération
            return self.verify_mt5_health()

    def verify_mt5_health(self):
        """Vérification spécifique MT5 - VERSION ROBUSTE"""
        try:
            # Vérifier si MT5 est initialisé
            if not mt5.initialize():
                logging.warning("🔄 Tentative de réinitialisation MT5...")
                if not self.connect_mt5_secure():
                    return False
            
            # Vérifier le compte
            account = mt5.account_info()
            if not account:
                logging.warning("🔄 Tentative de reconnexion compte MT5...")
                if not self.connect_mt5_secure():
                    return False
                account = mt5.account_info()
            
            return account is not None
            
        except Exception as e:
            logging.error(f"🔴 Erreur santé MT5: {e}")
            return False

    def run(self):
        """Boucle principale de trading avec logging amélioré"""
        logging.info("🚀 DÉMARRAGE MICRO SCALPING V8 PRO - SYSTÈME IA...")
        
        # Afficher l'en-tête
        self.print_trading_header()
        
        last_decision = datetime.now()
        last_health_check = datetime.now()
        last_status_report = datetime.now()
        last_config_check = datetime.now() 
        last_position_monitor = datetime.now() 
        
        try:
            while True:
                if not self.verify_connection():
                    time.sleep(2)
                    continue
                
                current_time = datetime.now()
                
                # ✅ AJOUT: Surveillance CONTINUE des positions (toutes les 2 secondes)
                if (current_time - last_position_monitor).seconds >= 2:
                    self.monitor_active_positions()
                    last_position_monitor = current_time
                
                # ✅ AJOUT: Vérification configuration dynamique
                if (current_time - last_config_check).seconds >= self.config_check_interval:
                    if hasattr(self, 'dynamic_config'):
                        self.dynamic_config.check_and_reload()
                    last_config_check = current_time
                
                # ✅ AJOUT: Nettoyage des données
                if hasattr(self, 'cleanup_old_data'):
                    self.cleanup_old_data()
                
                # RAPPORT DE STATUS TOUTES LES 30 SECONDES
                if (current_time - last_status_report).seconds >= 30:
                    self.get_realtime_status()
                    last_status_report = current_time
                
                # DÉCISION IA TOUTES LES 5 SECONDES
                if (current_time - last_decision).seconds >= 5:
                    signal = self.executer_strategie_micro_ia()
                    if signal:
                        if self.executer_trade(signal):
                            logging.info("✅ Trade exécuté avec succès")
                            # ✅ AJOUT: Enregistrement des métriques avancées
                            if hasattr(self, 'advanced_metrics'):
                                try:
                                    # Récupérer le profit du signal
                                    profit = signal.get('profit', 0)
                                    if profit == 0 and hasattr(signal, 'profit'):
                                        profit = signal.profit
                                    
                                    self.advanced_metrics.record_trade(
                                        profit=profit,
                                        confidence=signal.get('confidence', 0.5),
                                        volatility=signal.get('volatilite', 0.05)
                                    )
                                    
                                    # ✅ AJOUT: Log structuré
                                    if hasattr(self, 'structured_logger'):
                                        trade_event = TradeEvent(
                                            symbol=signal.get('symbol', 'UNKNOWN'),
                                            direction=signal.get('direction', 'UNKNOWN'),
                                            entry_price=signal.get('entry_price', 0),
                                            profit=profit,
                                            timestamp=datetime.now().isoformat(),
                                            confidence=signal.get('confidence', 0.5),
                                            volatility=signal.get('volatilite', 0.05),
                                            lot_size=signal.get('lot', 0)
                                        )
                                        self.structured_logger.log_trade_event(trade_event)
                                        
                                except Exception as e:
                                    logging.error(f"❌ Erreur enregistrement métriques: {e}")
                    last_decision = current_time
                
                # VÉRIFICATION SANTÉ TOUTES LES 30 SECONDES - VERSION CORRIGÉE
                if (current_time - last_health_check).seconds >= 30:
                    health_ok = self.perform_health_check()
                    if not health_ok:
                        logging.warning("🔄 Tentative de récupération automatique...")
                        # Reconnexion automatique
                        self.connect_mt5_secure()
                    last_health_check = current_time
                
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            logging.info("🛑 Arrêt demandé par l'utilisateur")
        except Exception as e:
            logging.error(f"💥 Erreur boucle principale: {e}")
        finally:
            self.shutdown()

    def shutdown(self):
        """Arrêt gracieux du système"""
        try:
            logging.info("🛑 Arrêt du système...")
            mt5.shutdown()
            logging.info("✅ Système arrêté avec succès")
        except Exception as e:
            logging.error(f"❌ Erreur lors de l'arrêt: {e}")

    def get_performance_report(self):
        """Génère un rapport de performance"""
        win_rate = (self.winning_trades / self.trade_count * 100) if self.trade_count > 0 else 0
        
        return {
            'total_trades': self.trade_count,
            'winning_trades': self.winning_trades,
            'initial_balance': self.initial_balance,
            'current_balance': self.account.balance if self.account else 0,
            'total_profit': (self.account.balance - self.initial_balance) if self.account else 0,
            'win_rate': win_rate,
            'uptime': str(datetime.now() - self.start_time),
            'micro_mode': self.micro_mode_actif,
            'security_status': self.security_manager.get_security_status(),
            'max_drawdown': self.performance_stats['max_drawdown']
        }
        
    # ✅ AJOUTER CETTE MÉTHODE APRÈS `get_performance_report`
    def get_advanced_performance_report(self):
        """Rapport de performance avancé"""
        try:
            base_report = self.get_performance_report()
            
            # Vérifier si advanced_metrics existe
            if hasattr(self, 'advanced_metrics'):
                advanced_report = self.advanced_metrics.get_performance_report()
            else:
                advanced_report = {
                    'sharpe_ratio': 0,
                    'max_drawdown': 0,
                    'win_rate': 0,
                    'avg_profit': 0,
                    'profit_factor': 0
                }
            
            return {**base_report, **advanced_report}
            
        except Exception as e:
            logging.error(f"❌ Erreur rapport performance avancé: {e}")
            return self.get_performance_report()        

# =============== FONCTIONS UTILITAIRES ===============
def analyser_volatilite_courante(symbol: str) -> Dict[str, Any]:
    """Analyse la volatilité avec calcul avancé"""
    try:
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 1)
        if rates is None or len(rates) == 0:
            return {'volatilite': 0.0, 'statut': 'INCONNU', 'range_absolu': 0.0}
        
        bougie = rates[0]
        high = bougie['high']
        low = bougie['low']
        
        def calculer_volatilite_reelle(high: float, low: float) -> float:
            if high <= low or high <= 0:
                return 0.0
            prix_moyen = (high + low) / 2
            range_absolu = high - low
            volatilite_pourcentage = (range_absolu / prix_moyen) * 100
            return round(volatilite_pourcentage, 3)
        
        volatilite = calculer_volatilite_reelle(high, low)
        range_absolu = high - low
        
        # ✅ CORRIGÉ : Utiliser VOLATILITE_CONFIG avec valeurs par défaut
        global_limits = VOLATILITE_CONFIG
        symbol_limits = VOLATILITE_CONFIG["BY_SYMBOL"].get(symbol, global_limits)
        
        extreme_limit = symbol_limits.get("EXTREME", global_limits.get("EXTREME", 0.15))
        max_limit = symbol_limits.get("MAX", global_limits.get("MAX", 0.10))
        min_limit = symbol_limits.get("MIN", global_limits.get("MIN", 0.02))
        
        if volatilite > extreme_limit:
            statut = "EXTRÊME 🔴"
        elif volatilite > max_limit:
            statut = "ÉLEVÉE 🟡"
        elif min_limit <= volatilite <= max_limit:
            statut = "IDÉALE 🟢"
        else:
            statut = "FAIBLE ⚪"
        
        return {
            'volatilite': volatilite,
            'statut': statut,
            'range_absolu': range_absolu,
            'high': high,
            'low': low,
            'close': bougie['close'],
            'prix_moyen': (high + low) / 2
        }
        
    except Exception as e:
        logging.error(f"❌ Erreur analyse volatilité: {e}")
        return {'volatilite': 0.5, 'statut': 'ERREUR', 'range_absolu': 0.0}

# =============== LANCEUR PRINCIPAL ===============
def parse_arguments():
    parser = argparse.ArgumentParser(description='BTCUSD Micro Scalper V8 PRO - Version IA')
    parser.add_argument('--real', action='store_true', help='Mode trading réel')
    parser.add_argument('--mode', choices=['MICRO', 'AGGRESSIVE', 'CONSERVATIVE'], 
                       default='MICRO', help='Mode de trading')
    parser.add_argument('--risk', type=float, default=0.5, help='Pourcentage de risque')
    parser.add_argument('--ai-enabled', action='store_true', default=True, help='Activer IA adaptative')
    return parser.parse_args()

def main():
    try:
        args = parse_arguments()
        
        bot = BTCUSDMicroScalperPro()
        
        if not bot.initialize(
            real_trading=args.real, 
            mode=args.mode
        ):
            logging.error("❌ Échec initialisation bot V8 PRO")
            return
            
        logging.info("🚀 DÉMARRAGE MICRO SCALPING V8 PRO - SYSTÈME IA...")
        
        last_decision = datetime.now()
        last_health_check = datetime.now()
        
        while True:
            try:
                if not bot.verify_connection():
                    time.sleep(2)
                    continue
                
                current_time = datetime.now()
                
                # DÉCISION IA TOUTES LES 3 SECONDES
                if (current_time - last_decision).seconds >= 3:
                    signal = bot.executer_strategie_micro_ia()
                    if signal:
                        bot.executer_trade(signal)
                    last_decision = current_time
                
                # VÉRIFICATION SANTÉ TOUTES LES 30 SECONDES
                if (current_time - last_health_check).seconds >= 30:
                    bot.perform_health_check()
                    last_health_check = current_time
                
                time.sleep(0.1)  # Réactivité maximale
                
            except KeyboardInterrupt:
                logging.info("🛑 Arrêt demandé par l'utilisateur")
                break
            except Exception as e:
                logging.error(f"💥 Erreur boucle principale: {e}")
                time.sleep(5)
                
    except Exception as e:
        logging.error(f"💥 ERREUR CRITIQUE: {e}")
        logging.error(traceback.format_exc())
    finally:
        try:
            mt5.shutdown()
            logging.info("✅ Session micro scalping V8 PRO terminée")
        except:
            pass
            
            # ████████████████████████████████████████████████████████████████████████████████
# AJOUTER APRÈS LA FONCTION main() - À LA FIN DU FICHIER
# ████████████████████████████████████████████████████████████████████████████████

def debug_symbols_availability():
    """Debug la disponibilité de tous les symboles"""
    print("\n" + "="*60)
    print("🔍 DEBUG DISPONIBILITÉ SYMBOLES")
    print("="*60)
    
    all_symbols = ["BTCUSD", "GOLD", "USDZAR", "EURUSD", "USDJPY", "GBPUSD", "AUDUSD", "NZDUSD"]
    
    for symbol in all_symbols:
        try:
            # Vérifier si le symbole existe
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                # Vérifier si activé
                if symbol_info.visible:
                    status = "✅ ACTIVÉ"
                else:
                    status = "⚠️ DÉSACTIVÉ"
                    # Tenter d'activer
                    mt5.symbol_select(symbol, True)
                    
                # Info spread et prix
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    spread = (tick.ask - tick.bid) * 10000  # Spread en pips
                    print(f"{symbol}: {status} | Spread: {spread:.1f} pips | Bid: {tick.bid:.5f}")
                else:
                    print(f"{symbol}: {status} | Données tick non disponibles")
            else:
                print(f"{symbol}: ❌ NON DISPONIBLE")
                
        except Exception as e:
            print(f"{symbol}: 💥 ERREUR: {e}")
    
    print("="*60)
    
    
# ✅ AJOUTEZ cette méthode à la fin de la classe BTCUSDMicroScalperPro

def test_rsi_logic(self):
    """Teste la logique RSI corrigée"""
    test_cases = [
        (80, "UP", "SELL"),     # RSI très haut + trend up = VENTE
        (20, "DOWN", "BUY"),    # RSI très bas + trend down = ACHAT  
        (55, "UP", "HOLD"),     # RSI neutre = pas de signal
        (65, "UP", "SELL"),     # RSI haut + trend up = VENTE
        (35, "DOWN", "BUY")     # RSI bas + trend down = ACHAT
    ]
    
    print("🧪 TEST LOGIQUE RSI CORRIGÉE")
    print("=" * 40)
    
    for rsi, trend, expected in test_cases:
        # Simulation de votre nouvelle logique
        direction = None
        if rsi > 75:
            direction = "SELL"
        elif rsi > 65 and trend == "UP":
            direction = "SELL"
        elif rsi < 25:
            direction = "BUY"
        elif rsi < 35 and trend == "DOWN":
            direction = "BUY"
            
        status = "✅" if direction == expected else "❌"
        print(f"{status} RSI: {rsi}, Trend: {trend} -> Résultat: {direction} (Attendu: {expected})")
    
    print("=" * 40)    

if __name__ == "__main__":
    main()
'''

# =================== VERSION STABLE (IA UNIQUEMENT) ===================

import argparse
import logging
import os
from typing import Any, Dict, Optional

import MetaTrader5 as mt5
import requests

AI_DECISION_URL = os.getenv("AI_ENGINE_URL", "http://127.0.0.1:5003/api/decision")
AI_HEALTH_URL = os.getenv("AI_ENGINE_HEALTH_URL", "http://127.0.0.1:5003/health")


class BTCUSDMicroScalperPro:
    def __init__(self):
        self.real_trading = False
        self.account = None
        self.active_symbols = [s for s, cfg in SYMBOLS_CONFIG.items() if cfg.get("enabled")]
        self.request_timeout = SECURITY_CONFIG.get("request_timeout", 5)
        self.last_trade_time: Optional[datetime] = None

    def initialize(self, real_trading: bool = False, mode: str = "MICRO") -> bool:
        self.real_trading = real_trading
        if not mt5.initialize():
            logging.error("❌ MT5 non initialisé")
            return False
        self.account = mt5.account_info()
        if not self.account:
            logging.error("❌ Impossible de récupérer le compte MT5")
            return False
        if not self.active_symbols:
            logging.error("❌ Aucun symbole actif")
            return False
        logging.info("✅ MT5 initialisé | Mode réel: %s", self.real_trading)
        return True

    def verify_connection(self) -> bool:
        try:
            return mt5.terminal_info() is not None and mt5.account_info() is not None
        except Exception:
            return False

    def _get_symbol_tick(self, symbol: str) -> Optional[Dict[str, Any]]:
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return None
        spread = (tick.ask - tick.bid) if tick.ask and tick.bid else 0
        return {
            "bid": tick.bid,
            "ask": tick.ask,
            "spread": spread,
            "volume": tick.volume,
            "time": tick.time,
        }

    def _build_payload(self, symbol: str) -> Optional[Dict[str, Any]]:
        tick = self._get_symbol_tick(symbol)
        if not tick:
            return None
        return {
            "context": "entry",
            "symbol": symbol,
            "bid": tick["bid"],
            "ask": tick["ask"],
            "spread": tick["spread"],
            "volume": tick["volume"],
            "timestamp": datetime.now().isoformat(),
            "risk": MICRO_SCALPING_CONFIG.get("risk_per_trade", 0.5),
        }

    def _request_ai_decision(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.post(
                AI_DECISION_URL,
                json=payload,
                timeout=self.request_timeout,
            )
            if resp.status_code != 200:
                logging.warning("⚠️ IA indisponible: %s", resp.text)
                return None
            data = resp.json()
            if not isinstance(data, dict):
                return None
            return data
        except Exception as e:
            logging.warning("⚠️ Erreur IA: %s", e)
            return None

    def executer_strategie_micro_ia(self) -> Optional[Dict[str, Any]]:
        for symbol in self.active_symbols:
            payload = self._build_payload(symbol)
            if not payload:
                continue
            decision = self._request_ai_decision(payload)
            if not decision:
                continue
            action = decision.get("action")
            if action in ("BUY", "SELL"):
                decision["symbol"] = symbol
                return decision
        return None

    def executer_trade(self, decision: Dict[str, Any]) -> bool:
        symbol = decision.get("symbol")
        action = decision.get("action")
        if not symbol or action not in ("BUY", "SELL"):
            return False

        if not self.real_trading:
            logging.info("[SIMU] %s %s", action, symbol)
            return True

        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info or not symbol_info.visible:
            mt5.symbol_select(symbol, True)

        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return False

        volume = SYMBOLS_CONFIG.get(symbol, {}).get("min_lot", 0.01)
        price = tick.ask if action == "BUY" else tick.bid
        sl = decision.get("sl_price")
        tp = decision.get("tp_price")

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "type_filling": mt5.ORDER_FILLING_IOC,
            "type_time": mt5.ORDER_TIME_GTC,
        }

        result = mt5.order_send(request)
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            logging.error("❌ Ordre rejeté: %s", result)
            return False
        logging.info("✅ Ordre exécuté: %s %s", action, symbol)
        return True

    def perform_health_check(self) -> bool:
        try:
            resp = requests.get(AI_HEALTH_URL, timeout=self.request_timeout)
            return resp.status_code == 200
        except Exception:
            return False

    def shutdown(self):
        try:
            mt5.shutdown()
        except Exception:
            pass


def parse_arguments():
    parser = argparse.ArgumentParser(description="BTCUSD Micro Scalper V8 PRO - IA")
    parser.add_argument("--real", action="store_true", help="Mode trading réel")
    parser.add_argument("--mode", choices=["MICRO", "AGGRESSIVE", "CONSERVATIVE"], default="MICRO")
    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    args = parse_arguments()

    bot = BTCUSDMicroScalperPro()
    if not bot.initialize(real_trading=args.real, mode=args.mode):
        logging.error("❌ Échec initialisation bot V8 PRO")
        return

    last_decision = datetime.now()
    last_health_check = datetime.now()

    try:
        while True:
            if not bot.verify_connection():
                time.sleep(2)
                continue

            now = datetime.now()

            if (now - last_decision).seconds >= 3:
                decision = bot.executer_strategie_micro_ia()
                if decision:
                    bot.executer_trade(decision)
                last_decision = now

            if (now - last_health_check).seconds >= 30:
                if not bot.perform_health_check():
                    logging.warning("⚠️ IA indisponible")
                last_health_check = now

            time.sleep(0.2)
    except KeyboardInterrupt:
        logging.info("🛑 Arrêt demandé")
    finally:
        bot.shutdown()


if __name__ == "__main__":
    main()