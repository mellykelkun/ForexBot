"""
CONFIGURATION MICRO SCALPING PRO MULTI-PAIRS - Capital 10$ Minimum
Avec gestion adaptative multi-pairs et multi-timeframes
"""

import os
from datetime import datetime
import json
from typing import Dict, List, Optional

# =============== CONFIGURATION MULTI-PAIRS & TIMEFRAMES ===============
SYMBOLS_CONFIG = {
    "BTCUSD": {
        "enabled": True,
        "risk_multiplier": 1.0,
        "max_lot": 0.05,
        "min_lot": 0.001,
        "preferred_timeframes": ['M1', 'M5', 'M15'],
        "spread_limits": {
            "max": 100.0,      # points
            "high": 50.0,
            "normal": 20.0,
            "ideal": 10.0
        },
        "volatility_profile": "HIGH",
        "trading_hours": "24/7"
    },
    "GOLD": {  # ⬅️ REMPLACER XAUUSD par GOLD
        "enabled": True,
        "risk_multiplier": 0.8,
        "max_lot": 0.02,
        "min_lot": 0.001,
        "preferred_timeframes": ['M5', 'M15', 'H1'],
        "spread_limits": {
            "max": 200.0,
            "high": 100.0,
            "normal": 50.0,
            "ideal": 25.0
        },
        "volatility_profile": "MEDIUM_HIGH",
        "trading_hours": "24/5"
    },
    "USDZAR": {
        "enabled": True,
        "risk_multiplier": 0.6,
        "max_lot": 0.01,
        "min_lot": 0.001,
        "preferred_timeframes": ['M15', 'H1', 'H4'],
        "spread_limits": {
            "max": 500.0,
            "high": 250.0,
            "normal": 100.0,
            "ideal": 50.0
        },
        "volatility_profile": "HIGH",
        "trading_hours": "24/5"
    },
    "EURUSD": {
        "enabled": True,
        "risk_multiplier": 1.0,
        "max_lot": 0.03,
        "min_lot": 0.001,
        "preferred_timeframes": ['M1', 'M5', 'M15'],
        "spread_limits": {
            "max": 20.0,
            "high": 10.0,
            "normal": 5.0,
            "ideal": 2.0
        },
        "volatility_profile": "LOW",
        "trading_hours": "24/5"
    },
    "USDJPY": {
        "enabled": True,
        "risk_multiplier": 0.9,
        "max_lot": 0.03,
        "min_lot": 0.001,
        "preferred_timeframes": ['M1', 'M5', 'M15'],
        "spread_limits": {
            "max": 25.0,
            "high": 12.0,
            "normal": 6.0,
            "ideal": 3.0
        },
        "volatility_profile": "LOW_MEDIUM",
        "trading_hours": "24/5"
    },
    "GBPUSD": {
        "enabled": True,
        "risk_multiplier": 0.8,
        "max_lot": 0.02,
        "min_lot": 0.001,
        "preferred_timeframes": ['M5', 'M15', 'H1'],
        "spread_limits": {
            "max": 25.0,
            "high": 12.0,
            "normal": 6.0,
            "ideal": 3.0
        },
        "volatility_profile": "MEDIUM",
        "trading_hours": "24/5"
    },
    "AUDUSD": {
        "enabled": True,
        "risk_multiplier": 0.9,
        "max_lot": 0.03,
        "min_lot": 0.001,
        "preferred_timeframes": ['M5', 'M15', 'H1'],
        "spread_limits": {
            "max": 25.0,
            "high": 12.0,
            "normal": 6.0,
            "ideal": 3.0
        },
        "volatility_profile": "MEDIUM",
        "trading_hours": "24/5"
    },
    "NZDUSD": {
        "enabled": True,
        "risk_multiplier": 0.7,
        "max_lot": 0.02,
        "min_lot": 0.001,
        "preferred_timeframes": ['M15', 'H1', 'H4'],
        "spread_limits": {
            "max": 30.0,
            "high": 15.0,
            "normal": 8.0,
            "ideal": 4.0
        },
        "volatility_profile": "MEDIUM",
        "trading_hours": "24/5"
    }
}

# Liste des symboles activés
SYMBOLS = [symbol for symbol, config in SYMBOLS_CONFIG.items() if config["enabled"]]

# Configuration des timeframes
TIMEFRAMES_CONFIG = {
    'M1': {
        "enabled": True,
        "weight": 0.3,
        "indicator_multiplier": 1,
        "min_bars": 20
    },
    'M5': {
        "enabled": True,
        "weight": 0.4,
        "indicator_multiplier": 1,
        "min_bars": 25
    },
    'M10': {
        "enabled": True,
        "weight": 0.2,
        "indicator_multiplier": 2,
        "min_bars": 30
    },
    'M15': {
        "enabled": True,
        "weight": 0.5,
        "indicator_multiplier": 3,
        "min_bars": 35
    },
    'H1': {
        "enabled": True,
        "weight": 0.6,
        "indicator_multiplier": 6,
        "min_bars": 40
    },
    'H4': {
        "enabled": True,
        "weight": 0.4,
        "indicator_multiplier": 24,
        "min_bars": 50
    },
    'D1': {
        "enabled": True,
        "weight": 0.3,
        "indicator_multiplier": 144,
        "min_bars": 60
    },
    'W1': {
        "enabled": False,  # Désactivé par défaut pour scalping
        "weight": 0.1,
        "indicator_multiplier": 1008,
        "min_bars": 80
    },
    'MN1': {
        "enabled": False,  # Désactivé par défaut pour scalping
        "weight": 0.05,
        "indicator_multiplier": 4320,
        "min_bars": 100
    }
}

# Mapping des timeframes MT5
TIMEFRAMES_MT5 = {
    'M1': 1,
    'M5': 5,
    'M10': 10,
    'M15': 15,
    'H1': 60,
    'H4': 240,
    'D1': 1440,
    'W1': 10080,
    'MN1': 43200
}

# =============== CONFIGURATION DE BASE MULTI-PAIRS ===============
MICRO_SCALPING_CONFIG = {
    "enabled": True,
    "capital_mini": 10.0,
    "capital_maxi": 35000.0,
    "risk_per_trade": 0.5,
    "take_profit_pips": 3,
    "stop_loss_pips": 5,
    "max_spread_pips": 2.5,
    "volatility_filter": True,
    "max_volatility_pips": 12,
    "cooldown_seconds": 6,
    "max_daily_trades": 60,
    "auto_stop_drawdown": 2.0,
    "lot_size_multiplier": 0.3,
    "required_confidence": 0.6,
    "adaptive_learning": True,
    "news_filter": True,
    "volume_filter": True,
    # NOUVEAUX PARAMÈTRES MULTI-PAIRS
    "max_concurrent_trades": 3,
    "symbol_rotation": True,
    "correlation_filter": True,
    "session_aware": True
}

# =============== CONFIGURATION SESSIONS DE TRADING ===============
TRADING_SESSIONS = {
    "ASIA": {
        "start": "00:00", "end": "08:00", 
        "active_symbols": ["USDJPY", "AUDUSD", "NZDUSD"],
        "aggressivity": 0.7  # Réduction en session asiatique
    },
    "LONDON_NY_OVERLAP": {
        "start": "13:00", "end": "16:00",
        "active_symbols": ["EURUSD", "GBPUSD", "GOLD", "USDZAR"],
        "aggressivity": 1.2  # Boost pendant le overlap
    }
}

# Paires disponibles 24/7
CRYPTO_SYMBOLS = ["BTCUSD"]

# =============== PARAMÈTRES VOLATILITÉ MULTI-PAIRS ===============
VOLATILITE_CONFIG = {
    "GLOBAL": {
        "MIN": 0.02,
        "MAX": 0.12,
        "EXTREME": 0.18,
        "ADAPTIVE": True
    },
    "BY_SYMBOL": {
        "BTCUSD": {"MIN": 0.05, "MAX": 0.20, "EXTREME": 0.30},
        "GOLD":   {"MIN": 0.03, "MAX": 0.15, "EXTREME": 0.25}, 
        "USDZAR": {"MIN": 0.08, "MAX": 0.25, "EXTREME": 0.40},
        "EURUSD": {"MIN": 0.01, "MAX": 0.08, "EXTREME": 0.15},
        "USDJPY": {"MIN": 0.02, "MAX": 0.10, "EXTREME": 0.18},
        "GBPUSD": {"MIN": 0.02, "MAX": 0.12, "EXTREME": 0.20},
        "AUDUSD": {"MIN": 0.02, "MAX": 0.10, "EXTREME": 0.18},
        "NZDUSD": {"MIN": 0.02, "MAX": 0.12, "EXTREME": 0.20}
    }
}

# AJOUTER pour plus de précision
VOLATILITY_ADJUSTMENTS = {
    "HIGH_VOLATILITY": {
        "lot_reduction": 0.6,
        "confidence_boost": 1.1,
        "wider_stops": True
    },
    "LOW_VOLATILITY": {
        "lot_boost": 1.2,
        "tighter_stops": True,
        "max_trades": 30
    }
}

# =============== INDICATEURS AVANCÉS MULTI-TIMEFRAMES ===============
INDICATEURS_CONFIG = {
    "BASE": {
        "ema_very_fast": 3,
        "ema_fast": 5,
        "ema_slow": 12,
        "rsi_period": 7,
        "rsi_overbought": 68, 
        "rsi_oversold": 32,
        "stoch_period": 5,
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
        "bollinger_period": 20,
        "bollinger_std": 2,
        "stoch_k": 14, 
        "stoch_d": 3,
        "atr_period": 7,
        "volume_ma_period": 10
    },
    "TIMEFRAME_MULTIPLIERS": {
        'M1': 1, 'M5': 1, 'M10': 1, 'M15': 1,
        'H1': 4, 'H4': 8, 'D1': 24, 'W1': 120, 'MN1': 480
    },
    "SYMBOL_SPECIFIC": {
        "GOLD": {
            "atr_multiplier": 1.5,  # GOLD est plus volatile
            "rsi_period": 10,
            "bollinger_std": 2.5
        },
        "BTCUSD": {
            "atr_multiplier": 2.0,
            "rsi_period": 7
        }
    }
}


# =============== PARAMÈTRES IA ADAPTATIVE ===============
AI_ADAPTIVE_CONFIG = {
    "enabled": True,
    "learning_rate": 0.1,
    "performance_memory": 100,
    "required_confidence": 0.6,
    # Nombre de trades mémorisés
    "parameter_optimization": True,
    "market_regime_detection": True,
    "confidence_boost": True
}

# =============== CONFIGURATION SÉCURITÉ ===============
SECURITY_CONFIG = {
    "max_consecutive_losses": 5,
    "daily_loss_limit": 5.0,
    "weekly_loss_limit": 10.0,
    "auto_stop_enabled": True,
    "connection_timeout": 10,
    "request_timeout": 5
}

# AJOUTER ces paramètres
ADVANCED_SECURITY = {
    "hourly_trade_limit": 15,           # Max 15 trades/heure
    "consecutive_wins_stop": 10,        # Stop après 10 gains consécutifs
    "volume_spike_protection": True,    # Protection spikes de volume
    "news_event_filter": True,          # Filtre événements économiques
    "correlation_limit": 0.8            # Évite trades corrélés
}

# =============== CONFIGURATION SORTIE INTELLIGENTE ===============
INTELLIGENT_EXIT_CONFIG = {
    "enabled": False,
    "no_fixed_sl_tp": True,  # Pas de SL/TP fixes
    
    # Seuils de décision
    "exit_probability_threshold": 0.75,      # Seuil de probabilité de sortie
    "min_confidence_threshold": 0.4,         # Confiance minimale pour rester
    "emergency_exit_threshold": 0.85,        # Sortie d'urgence
    
    # Facteurs de décision (poids)
    "weights": {
        "ai_confidence": 0.25,               # Confiance IA adaptative
        "candle_reversal": 0.20,             # Patterns de chandeliers
        "momentum_weakening": 0.15,          # Affaiblissement momentum
        "profit_protection": 0.05            # Protection des profits
    },
    
    # Micro-scalping intelligent
    "micro_scalping_exit": {
        "max_position_age_minutes": 30,      # Âge max d'une position
        "profit_reduction_threshold": 0.7,   # Si profit diminue de 30%
        "min_profit_target": 0.001,          # 0.1% profit minimum
        "max_loss_tolerance": -0.0005        # -0.05% perte max
    },
    
    # Détection des retournements
    "reversal_detection": {
        "candle_patterns_enabled": True,
        "rsi_divergence": True,
        "momentum_shift": True,
        "volume_spike_detection": True
    },
    
    # Paramètres d'apprentissage
    "learning": {
        "experience_memory_size": 5000,
        "reward_successful_exits": 1.0,
        "penalize_late_exits": -1.0,
        "reward_profit_protection": 0.5,
        "auto_save_interval": 100
    },
    
    # Monitoring en temps réel
    "monitoring": {
        "check_interval_seconds": 2,         # Vérification toutes les 2s
        "position_health_check": True,
        "real_time_analysis": True
    }
}

# =============== CONFIGURATION GUARDIAN SYSTEM ===============
GUARDIAN_SYSTEM_CONFIG = {
    "enabled": False,
    "continuous_monitoring": True,
    
    # Surveillance multi-critères
    "monitoring_factors": {
        "price_action": True,
        "indicator_divergence": True,
        "volume_analysis": True,
        "volatility_spikes": True,
        "time_based_exits": True
    },
    
    # Détection de momentum
    "momentum_analysis": {
        "short_term_period": 5,      # 5 périodes pour court terme
        "medium_term_period": 10,    # 10 périodes pour moyen terme
        "trend_confirmation": True,
        "momentum_threshold": 0.05   # Seuil de changement de momentum
    },
    
    # Analyse des bougies
    "candlestick_analysis": {
        "reversal_patterns": [
            "BEARISH_ENGULFING", "BULLISH_ENGULFING", "SHOOTING_STAR", 
            "HAMMER", "DARK_CLOUD_COVER", "PIERCING_LINE", 
            "EVENING_STAR", "MORNING_STAR"
        ],
        "strength_threshold": 0.6,
        "volume_confirmation": True
    },
    
    # Protection des profits
    "profit_protection": {
        "trailing_mental_stop": True,
        "dynamic_exit_points": True,
        "profit_secure_levels": [0.001, 0.002, 0.005],  # 0.1%, 0.2%, 0.5%
        "auto_secure_at": 0.003                          # Sécuriser auto à 0.3%
    }
}

# =============== CONFIGURATION ANALYSE SORTIE MULTI-TIMEFRAME ===============
EXIT_MULTI_TIMEFRAME_CONFIG = {
    "enabled": True,
    
    # Timeframes pour confirmation de sortie
    "exit_timeframes": {
        "primary": "M1",        # Décision principale
        "confirmation": "M5",   # Confirmation
        "trend": "M15"          # Contexte tendance
    },
    
    # Poids des timeframes dans la décision
    "timeframe_weights": {
        "M1": 0.4,
        "M5": 0.3, 
        "M15": 0.2,
        "H1": 0.1
    },
    
    # Critères par timeframe
    "exit_criteria": {
        "M1": {
            "momentum_change": True,
            "immediate_reversal": True,
            "spike_detection": True
        },
        "M5": {
            "pattern_confirmation": True,
            "trend_break": True,
            "support_resistance": True
        },
        "M15": {
            "trend_context": True,
            "volume_analysis": True,
            "market_structure": True
        }
    }
}

# =============== CONFIGURATION SORTIE PAR SYMBOLE ===============
SYMBOL_EXIT_RULES = {
    "BTCUSD": {
        "volatility_adjustment": 1.2,
        "quick_exit_enabled": True,
        "max_position_age": 45,      # 45 minutes max
        "profit_targets": [0.001, 0.002, 0.005],
        "emergency_exit_volatility": 0.25
    },
    "GOLD": {
        "volatility_adjustment": 1.1,
        "quick_exit_enabled": True,
        "max_position_age": 60,      # 1 heure max
        "profit_targets": [0.0015, 0.003, 0.008],
        "emergency_exit_volatility": 0.20
    },
    "USDZAR": {
        "volatility_adjustment": 1.5,
        "quick_exit_enabled": False,  # Désactivé pour haute volatilité
        "max_position_age": 30,       # 30 minutes max
        "profit_targets": [0.002, 0.004, 0.010],
        "emergency_exit_volatility": 0.35
    },
    "EURUSD": {
        "volatility_adjustment": 0.9,
        "quick_exit_enabled": True,
        "max_position_age": 90,       # 1h30 max
        "profit_targets": [0.0005, 0.001, 0.002],
        "emergency_exit_volatility": 0.12
    },
    "USDJPY": {
        "volatility_adjustment": 0.8,
        "quick_exit_enabled": True,
        "max_position_age": 75,       # 1h15 max
        "profit_targets": [0.0006, 0.0012, 0.0025],
        "emergency_exit_volatility": 0.15
    }
}

# Ajoute cette section à la fin du fichier
SPREAD_CONFIG = {
    "max_spread": 0.1000,          # 100 points MAXIMUM
    "ideal_spread": 0.00200,        # 20 points idéal
    "high_spread": 0.00500,         # 50 points = alerte
    "spread_reduction_factor": 0.5, # Réduction de 50% si spread élevé
    "spread_boost_factor": 1.1,     # Léger boost si spread bas
    "spread_monitoring": True
}

# =============== CONFIGURATION CHANDELIERS JAPONAIS ===============
CANDLESTICK_CONFIG = {
    "enabled": True,
    "min_confidence": 0.7,
    "patterns_weight": 0.4,  # Poids dans la décision finale
    "required_volume": True,
    "timeframes": ['M5', 'M15', 'H1'],  # Timeframes pour l'analyse
    
    "pattern_strengths": {
        "STRONG_BULLISH": ["BULLISH_ENGULFING", "MORNING_STAR", "THREE_WHITE_SOLDIERS"],
        "MODERATE_BULLISH": ["HAMMER", "PIERCING_LINE", "INVERTED_HAMMER"],
        "STRONG_BEARISH": ["BEARISH_ENGULFING", "EVENING_STAR", "THREE_BLACK_CROWS"],
        "MODERATE_BEARISH": ["SHOOTING_STAR", "HANGING_MAN", "DARK_CLOUD_COVER"],
        "NEUTRAL": ["DOJI", "SPINNING_TOP"]
    },
    
    "confirmation_rules": {
        "require_volume_confirmation": True,
        "require_trend_alignment": True,
        "min_body_ratio": 0.3,
        "max_wick_ratio": 0.7
    }
}

def get_indicators_for_timeframe(timeframe: str) -> dict:
    """Retourne les paramètres d'indicateurs adaptés au timeframe"""
    base = INDICATEURS_CONFIG["BASE"].copy()
    multiplier = INDICATEURS_CONFIG["TIMEFRAME_MULTIPLIERS"].get(timeframe, 1)
    
    # Ajustement des périodes selon le timeframe
    adjusted = {}
    for key, value in base.items():
        if "period" in key or "fast" in key or "slow" in key or "signal" in key:
            adjusted[key] = max(3, int(value * multiplier))
        else:
            adjusted[key] = value
    
    return adjusted

# =============== FONCTIONS UTILITAIRES MULTI-PAIRS ===============
def get_mt5_timeframe(timeframe_str: str) -> int:
    """Convertit un timeframe string en valeur MT5"""
    return TIMEFRAMES_MT5.get(timeframe_str, 1)

def get_preferred_timeframes(symbol: str) -> list:
    """Retourne les timeframes préférés pour un symbole"""
    symbol_config = SYMBOLS_CONFIG.get(symbol, SYMBOLS_CONFIG["BTCUSD"])
    return [tf for tf in symbol_config["preferred_timeframes"] 
            if TIMEFRAMES_CONFIG.get(tf, {}).get("enabled", False)]

def is_symbol_enabled(symbol: str) -> bool:
    """Vérifie si un symbole est activé"""
    return symbol in SYMBOLS

def get_all_enabled_timeframes() -> list:
    """Retourne tous les timeframes activés"""
    return [tf for tf, config in TIMEFRAMES_CONFIG.items() 
            if config.get("enabled", False)]

def calculate_position_size(symbol: str, capital: float, stop_distance: float) -> float:
    """Calcule la taille de position adaptée au symbole"""
    symbol_config = SYMBOLS_CONFIG.get(symbol, SYMBOLS_CONFIG["BTCUSD"])
    risk_amount = capital * (MICRO_SCALPING_CONFIG["risk_per_trade"] / 100.0)
    risk_amount *= symbol_config["risk_multiplier"]
    
    # Calcul de base du lot
    base_lot = risk_amount / (stop_distance * 10)
    
    # Application des limites du symbole
    min_lot = symbol_config["min_lot"]
    max_lot = symbol_config["max_lot"]
    
    return max(min_lot, min(base_lot, max_lot))
    
# ... tout votre code existant ...

# ✅ AJOUTEZ cette section AVANT la classe Config

RSI_CONFIG = {
    "oversold": 30,
    "overbought": 70,
    "strong_oversold": 25,
    "strong_overbought": 75,
    "neutral_low": 40,
    "neutral_high": 60,
    "period": 14,
    "confidence_multiplier": 0.8
}

# =============== CONFIGURATION CHANDELIERS JAPONAIS AVANCÉE ===============
CANDLESTICK_CONFIG = {
    "enabled": True,
    "min_confidence": 0.7,
    "patterns_weight": 0.6,  # Poids majoritaire dans la décision
    "required_volume": True,
    "timeframes": ['M5', 'M15', 'H1', 'H4'],  # Timeframes pour l'analyse
    
    "pattern_strengths": {
        "STRONG_BULLISH": ["BULLISH_ENGULFING", "MORNING_STAR", "PIERCING_LINE", "THREE_WHITE_SOLDIERS", "HAMMER", "INVERTED_HAMMER"],
        "MODERATE_BULLISH": ["BULLISH_HARAMI", "BULLISH_DOJI_STAR", "BULLISH_KICKING"],
        "STRONG_BEARISH": ["BEARISH_ENGULFING", "EVENING_STAR", "DARK_CLOUD_COVER", "THREE_BLACK_CROWS", "SHOOTING_STAR", "HANGING_MAN"],
        "MODERATE_BEARISH": ["BEARISH_HARAMI", "BEARISH_DOJI_STAR", "BEARISH_KICKING"],
        "REVERSAL_NEUTRAL": ["DOJI", "LONG_LEGGED_DOJI", "DRAGONFLY_DOJI", "GRAVESTONE_DOJI", "SPINNING_TOP"]
    },
    
    "confirmation_rules": {
        "require_volume_confirmation": True,
        "require_trend_alignment": True,
        "min_body_ratio": 0.3,
        "max_wick_ratio": 0.7,
        "multi_timeframe_confirmation": True
    },
    
    "volume_analysis": {
        "enabled": True,
        "min_volume_ratio": 1.2,
        "volume_sma_period": 20
    }
}

# =============== CONFIGURATION ANALYSE MULTI-TIMEFRAME ===============
MULTI_TIMEFRAME_ANALYSIS = {
    "enabled": True,
    "primary_timeframe": "M5",
    "confirmation_timeframes": ["M15", "H1"],
    "trend_timeframes": ["H4", "D1"],
    "weights": {
        "primary": 0.4,
        "confirmation": 0.3,
        "trend": 0.3
    }
}

# =============== CONFIGURATION SUPPORT/RÉSISTANCE ===============
SUPPORT_RESISTANCE_CONFIG = {
    "enabled": True,
    "pivot_period": 20,
    "fibonacci_levels": [0.236, 0.382, 0.5, 0.618, 0.786],
    "volume_profile": True,
    "dynamic_levels": True
}
# =============== FONCTIONS UTILITAIRES MULTI-PAIRS ===============

def verify_gold_symbol():
    """Vérifie la disponibilité de GOLD et propose des alternatives"""
    import MetaTrader5 as mt5
    
    gold_symbols = ["GOLD", "XAUUSD", "XAUUSDm", "GOLDm", "XAUUSDe", "Gold"]
    available_gold = []
    
    for symbol in gold_symbols:
        if mt5.symbol_info(symbol):
            available_gold.append(symbol)
            print(f"✅ Symbole OR disponible: {symbol}")
    
    if available_gold:
        # Utiliser le premier symbole disponible
        recommended_gold = available_gold[0]
        print(f"🎯 Symbole OR recommandé: {recommended_gold}")
        return recommended_gold
    else:
        print("❌ Aucun symbole OR trouvé - Désactivation de GOLD")
        # Désactiver GOLD dans la configuration
        SYMBOLS_CONFIG["GOLD"]["enabled"] = False
        return None

def initialize_symbols_with_fallback():
    """Initialise les symboles avec fallback pour GOLD"""
    # Vérifier GOLD au démarrage
    gold_symbol = verify_gold_symbol()
    
    if gold_symbol and gold_symbol != "GOLD":
        # Mettre à jour la configuration avec le bon symbole
        SYMBOLS_CONFIG[gold_symbol] = SYMBOLS_CONFIG["GOLD"].copy()
        SYMBOLS_CONFIG["GOLD"]["enabled"] = False
        print(f"🔄 Utilisation de {gold_symbol} au lieu de GOLD")
    
    # Retourner la liste des symboles activés
    return [symbol for symbol, config in SYMBOLS_CONFIG.items() if config["enabled"]]

# REMPLACER l'ancienne ligne :
# SYMBOLS = [symbol for symbol, config in SYMBOLS_CONFIG.items() if config["enabled"]]

# PAR :
SYMBOLS = initialize_symbols_with_fallback()

# Puis ajoutez RSI_CONFIG dans la classe Config plus bas :

class Config:
    """
    Classe de configuration principale pour l'import dans main.py
    Version wrapper pour la compatibilité
    """
    
    def __init__(self):
        self.symbols = SYMBOLS
        self.timeframes = [tf for tf, config in TIMEFRAMES_CONFIG.items() if config.get("enabled", False)]
        self.micro_scalping = MICRO_SCALPING_CONFIG
        self.volatilite = VOLATILITE_CONFIG
        self.indicateurs = INDICATEURS_CONFIG
        self.ai_adaptive = AI_ADAPTIVE_CONFIG
        self.security = SECURITY_CONFIG
        self.spread = SPREAD_CONFIG
        self.symbols_config = SYMBOLS_CONFIG
        self.timeframes_config = TIMEFRAMES_CONFIG
        self.trading_sessions = TRADING_SESSIONS
        self.rsi_config = RSI_CONFIG
        self.intelligent_exit = INTELLIGENT_EXIT_CONFIG
        self.guardian_system = GUARDIAN_SYSTEM_CONFIG
        self.exit_multi_timeframe = EXIT_MULTI_TIMEFRAME_CONFIG
        self.symbol_exit_rules = SYMBOL_EXIT_RULES
        
        self.TRADING_MODE = 'PAPER'
        
        # ⭐ AJOUTEZ CES ATTRIBUTS MANQUANTS ⭐
        self.TRADING_MODE = 'PAPER'
        self.RISK_PER_TRADE = 0.5
        self.INITIAL_CAPITAL = 1000.0
        self.MICRO_SCALPING_ENABLED = True
        self.SCALPING_ENABLED = False
        self.SWING_TRADING_ENABLED = False
        self.MAX_MICRO_TRADES_PER_DAY = 50
        self.MT5_LOGIN = 123456
        self.MT5_PASSWORD = "password"
        self.MT5_SERVER = "BrokerServer"
        self.SYMBOL = "BTCUSD"
        
        self.GOLD_SYMBOL = self.detect_gold_symbol()
        
    def detect_gold_symbol(self):
        """Détecte le symbole correct pour l'or"""
        try:
            import MetaTrader5 as mt5
            gold_symbols = ["GOLD", "XAUUSD", "XAUUSDm", "GOLDm", "XAUUSDe"]
            for symbol in gold_symbols:
                if mt5.symbol_info(symbol):
                    return symbol
            return "GOLD"  # Fallback
        except:
            return "GOLD"
        
        try:
            import MetaTrader5 as mt5
            gold_symbols = ["GOLD", "XAUUSD", "XAUUSDm", "GOLDm", "XAUUSDe"]
            for symbol in gold_symbols:
                if mt5.symbol_info(symbol):
                    return symbol
            return "GOLD"  # Fallback
        except:
            return "GOLD"
            
    def test_configuration():
        """Teste la configuration multi-symboles"""
        print("\n" + "="*50)
        print("🧪 TEST CONFIGURATION MULTI-SYMBOLES")
        print("="*50)
        
        print(f"🎯 Symboles activés: {len(SYMBOLS)}")
        for symbol in SYMBOLS:
            config = SYMBOLS_CONFIG.get(symbol, {})
            print(f"   📊 {symbol}: Risque ×{config.get('risk_multiplier', 1.0)} | Lot max: {config.get('max_lot', 0)}")
        
        # Vérification spécifique GOLD
        if "GOLD" in SYMBOLS:
            print("✅ GOLD activé dans la configuration")
        else:
            print("❌ GOLD désactivé - vérifiez la disponibilité chez votre broker")
        
        print("="*50)

    # Appeler le test au chargement
    test_configuration()
    
    def get(self, key, default=None):
        """Accès aux paramètres comme un dict"""
        return getattr(self, key, default)
    
    def __getitem__(self, key):
        """Accès via [] comme un dict"""
        return getattr(self, key)
    
    def __contains__(self, key):
        """Vérification d'existence"""
        return hasattr(self, key)

class ConfigManager:
    """Gestionnaire de configuration dynamique multi-pairs"""
    
    def __init__(self):
        self.config_file = "trading_config.json"
        self.load_config()
    
    def load_config(self):
        """Charge la configuration depuis le fichier"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f: 
                    saved_config = json.load(f)
                    self.update_configs(saved_config)
        except Exception as e:
            print(f"⚠️ Erreur chargement config: {e}")
    
    def save_config(self):
        """Sauvegarde la configuration actuelle"""
        try:
            config_data = {
                'micro_scalping': MICRO_SCALPING_CONFIG,
                'volatilite': VOLATILITE_CONFIG,
                'indicateurs': INDICATEURS_CONFIG,
                'ai_adaptive': AI_ADAPTIVE_CONFIG,
                'security': SECURITY_CONFIG,
                'spread': SPREAD_CONFIG,
                'symbols': SYMBOLS_CONFIG,
                'timeframes': TIMEFRAMES_CONFIG,
                'trading_sessions': TRADING_SESSIONS,
                'intelligent_exit': INTELLIGENT_EXIT_CONFIG,
                'guardian_system': GUARDIAN_SYSTEM_CONFIG,
                'exit_multi_timeframe': EXIT_MULTI_TIMEFRAME_CONFIG,
                'symbol_exit_rules': SYMBOL_EXIT_RULES,
                'last_update': datetime.now().isoformat()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"❌ Erreur sauvegarde config: {e}")
    
    def update_configs(self, new_config):
        """Met à jour les configurations"""
        global MICRO_SCALPING_CONFIG, VOLATILITE_CONFIG, INDICATEURS_CONFIG
        global AI_ADAPTIVE_CONFIG, SECURITY_CONFIG, SPREAD_CONFIG
        global SYMBOLS_CONFIG, TIMEFRAMES_CONFIG, TRADING_SESSIONS
        
        MICRO_SCALPING_CONFIG.update(new_config.get('micro_scalping', {}))
        VOLATILITE_CONFIG.update(new_config.get('volatilite', {}))
        INDICATEURS_CONFIG.update(new_config.get('indicateurs', {}))
        AI_ADAPTIVE_CONFIG.update(new_config.get('ai_adaptive', {}))
        SECURITY_CONFIG.update(new_config.get('security', {}))
        SPREAD_CONFIG.update(new_config.get('spread', {}))
        SYMBOLS_CONFIG.update(new_config.get('symbols', {}))
        TIMEFRAMES_CONFIG.update(new_config.get('timeframes', {}))
        TRADING_SESSIONS.update(new_config.get('trading_sessions', {}))
        INTELLIGENT_EXIT_CONFIG.update(new_config.get('intelligent_exit', {}))
        GUARDIAN_SYSTEM_CONFIG.update(new_config.get('guardian_system', {}))
        EXIT_MULTI_TIMEFRAME_CONFIG.update(new_config.get('exit_multi_timeframe', {}))
        SYMBOL_EXIT_RULES.update(new_config.get('symbol_exit_rules', {}))
        
    def get_intelligent_exit_parameters(self, symbol: str, market_conditions: Dict) -> Dict:
        """Retourne les paramètres de sortie intelligente adaptés"""
        symbol_rules = SYMBOL_EXIT_RULES.get(symbol, SYMBOL_EXIT_RULES["BTCUSD"])
        volatility = market_conditions.get('volatilite', 0.05)
        
        # Ajustement dynamique basé sur la volatilité
        volatility_factor = symbol_rules.get('volatility_adjustment', 1.0)
        if volatility > 0.15:
            volatility_factor *= 0.8
        elif volatility < 0.03:
            volatility_factor *= 1.2
            
        return {
            'exit_probability_threshold': INTELLIGENT_EXIT_CONFIG['exit_probability_threshold'] * volatility_factor,
            'quick_exit_enabled': symbol_rules.get('quick_exit_enabled', True),
            'max_position_age': symbol_rules.get('max_position_age', 30),
            'profit_targets': symbol_rules.get('profit_targets', [0.001, 0.002, 0.005]),
            'volatility_adjustment': volatility_factor
        }
    
    def get_adaptive_parameters(self, market_conditions):
        """Retourne les paramètres adaptés aux conditions marché"""
        volatility = market_conditions.get('volatilite', 0.05)
        symbol = market_conditions.get('symbol', 'BTCUSD')
        
        # Ajustement dynamique basé sur volatilité et symbole
        symbol_config = SYMBOLS_CONFIG.get(symbol, SYMBOLS_CONFIG["BTCUSD"])
        base_risk = symbol_config["risk_multiplier"]
        
        if volatility > 0.15:
            return {
                'risk_multiplier': base_risk * 0.7,
                'confidence_threshold': 0.8,
                'cooldown_extended': True
            }
        elif volatility < 0.03:
            return {
                'risk_multiplier': base_risk * 0.5,
                'confidence_threshold': 0.7,
                'cooldown_extended': False
            }
        else:
            return {
                'risk_multiplier': base_risk,
                'confidence_threshold': 0.75,
                'cooldown_extended': False
            }
            
    def test_intelligent_exit_configuration():
        """Teste la configuration de sortie intelligente"""
        print("\n" + "="*60)
        print("🧪 TEST CONFIGURATION SORTIE INTELLIGENTE")
        print("="*60)
        
        print(f"🎯 Sortie intelligente: {'ACTIVÉE' if INTELLIGENT_EXIT_CONFIG['enabled'] else 'DÉSACTIVÉE'}")
        print(f"📊 Seuil probabilité sortie: {INTELLIGENT_EXIT_CONFIG['exit_probability_threshold']}")
        print(f"🛡️  Système Guardian: {'ACTIVÉ' if GUARDIAN_SYSTEM_CONFIG['enabled'] else 'DÉSACTIVÉ'}")
        
        # Test par symbole
        for symbol in ["BTCUSD", "GOLD", "EURUSD"]:
            if symbol in SYMBOL_EXIT_RULES:
                rules = SYMBOL_EXIT_RULES[symbol]
                print(f"   📈 {symbol}: Âge max {rules['max_position_age']}min | Sortie rapide: {'OUI' if rules['quick_exit_enabled'] else 'NON'}")
        
        print("="*60)

    # Appeler le test au chargement
    test_intelligent_exit_configuration()

    def get_symbol_exit_rules(symbol: str) -> Dict:
        """Retourne les règles de sortie pour un symbole spécifique"""
        return SYMBOL_EXIT_RULES.get(symbol, SYMBOL_EXIT_RULES["BTCUSD"])

    def is_quick_exit_enabled(symbol: str) -> bool:
        """Vérifie si la sortie rapide est activée pour un symbole"""
        rules = get_symbol_exit_rules(symbol)
        return rules.get('quick_exit_enabled', True)

    def get_max_position_age(symbol: str) -> int:
        """Retourne l'âge maximum d'une position pour un symbole"""
        rules = get_symbol_exit_rules(symbol)
        return rules.get('max_position_age', 30)

# Instance globale de configuration
config = Config()
# Instance globale
config_manager = ConfigManager()
__all__ = ['Config', 'config', 'config_manager']