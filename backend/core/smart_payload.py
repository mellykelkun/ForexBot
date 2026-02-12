"""
SMART PAYLOAD — Compression sémantique du payload pour l'IA
ForexBot SaaS

Au lieu d'envoyer 8000+ barres brutes (coûteux en tokens), 
on envoie une INTELLIGENCE CONDENSÉE :
  - État du marché (trend, volatilité, momentum)
  - Scores de confluence des indicateurs
  - Niveaux clés (support/résistance, Fibonacci)
  - Contexte de risque
  - Résumé multi-timeframe
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from backend.core import indicators as ind

logger = logging.getLogger("SmartPayload")


def classify_trend(ema_fast: float, ema_mid: float, ema_slow: float, price: float) -> Dict[str, Any]:
    """Classifie la tendance en une structure sémantique."""
    direction = "NEUTRAL"
    strength = 0

    if ema_fast > ema_mid > ema_slow:
        direction = "BULLISH"
        strength = 3
    elif ema_fast < ema_mid < ema_slow:
        direction = "BEARISH"
        strength = 3
    elif ema_fast > ema_mid:
        direction = "BULLISH"
        strength = 2
    elif ema_fast < ema_mid:
        direction = "BEARISH"
        strength = 2

    # Position du prix par rapport aux EMAs
    above_count = sum(1 for e in [ema_fast, ema_mid, ema_slow] if price > e)
    
    return {
        "direction": direction,
        "strength": strength,  # 0-3
        "ema_alignment": "PERFECT" if strength == 3 else "PARTIAL" if strength == 2 else "NONE",
        "price_vs_ema": f"{above_count}/3 above",
        "ema_spread_pct": round(abs(ema_fast - ema_slow) / max(ema_slow, 0.0001) * 100, 3),
    }


def classify_volatility(
    atr: float, price: float,
    bb_upper: float, bb_lower: float, bb_mid: float,
) -> Dict[str, Any]:
    """Classifie la volatilité."""
    atr_pct = (atr / max(price, 0.0001)) * 100
    bb_width = (bb_upper - bb_lower) / max(bb_mid, 0.0001) * 100

    if atr_pct < 0.1:
        regime = "VERY_LOW"
    elif atr_pct < 0.3:
        regime = "LOW"
    elif atr_pct < 0.8:
        regime = "MODERATE"
    elif atr_pct < 1.5:
        regime = "HIGH"
    else:
        regime = "EXTREME"

    # Position dans les bandes de Bollinger
    if bb_upper != bb_lower:
        bb_position = (price - bb_lower) / (bb_upper - bb_lower)
    else:
        bb_position = 0.5

    return {
        "regime": regime,
        "atr_pct": round(atr_pct, 4),
        "bb_width_pct": round(bb_width, 4),
        "price_in_bb": round(bb_position, 3),  # 0=lower, 0.5=mid, 1=upper
        "squeeze": bool(bb_width < 1.5),  # Bollinger squeeze
    }


def classify_momentum(
    rsi: float,
    macd_hist: float,
    stoch_k: float,
    stoch_d: float,
    mfi: Optional[float] = None,
) -> Dict[str, Any]:
    """Classifie le momentum."""
    # RSI classification
    if rsi > 80:
        rsi_zone = "EXTREME_OVERBOUGHT"
    elif rsi > 70:
        rsi_zone = "OVERBOUGHT"
    elif rsi < 20:
        rsi_zone = "EXTREME_OVERSOLD"
    elif rsi < 30:
        rsi_zone = "OVERSOLD"
    elif rsi > 55:
        rsi_zone = "BULLISH"
    elif rsi < 45:
        rsi_zone = "BEARISH"
    else:
        rsi_zone = "NEUTRAL"

    # MACD momentum
    macd_dir = "BULLISH" if macd_hist > 0 else "BEARISH" if macd_hist < 0 else "FLAT"

    # Stochastic cross
    stoch_cross = "NONE"
    if stoch_k > stoch_d and stoch_k < 30:
        stoch_cross = "BULLISH_CROSS_OVERSOLD"
    elif stoch_k < stoch_d and stoch_k > 70:
        stoch_cross = "BEARISH_CROSS_OVERBOUGHT"
    elif stoch_k > stoch_d:
        stoch_cross = "BULLISH"
    elif stoch_k < stoch_d:
        stoch_cross = "BEARISH"

    result = {
        "rsi": round(rsi, 2),
        "rsi_zone": rsi_zone,
        "macd_histogram": round(macd_hist, 6),
        "macd_direction": macd_dir,
        "stochastic_k": round(stoch_k, 2),
        "stochastic_d": round(stoch_d, 2),
        "stochastic_signal": stoch_cross,
    }

    if mfi is not None:
        result["mfi"] = round(mfi, 2)
        result["mfi_zone"] = (
            "OVERBOUGHT" if mfi > 80 else "OVERSOLD" if mfi < 20 else "NEUTRAL"
        )

    return result


def compute_confluence_score(
    trend: Dict, momentum: Dict, volatility: Dict,
) -> Dict[str, Any]:
    """Score de confluence — combien d'indicateurs sont d'accord."""
    bull_signals = 0
    bear_signals = 0

    # Trend contribution
    if trend["direction"] == "BULLISH":
        bull_signals += trend["strength"]
    elif trend["direction"] == "BEARISH":
        bear_signals += trend["strength"]

    # RSI contribution
    if momentum["rsi_zone"] in ("BULLISH", "EXTREME_OVERSOLD", "OVERSOLD"):
        bull_signals += 1
    elif momentum["rsi_zone"] in ("BEARISH", "EXTREME_OVERBOUGHT", "OVERBOUGHT"):
        bear_signals += 1

    # MACD contribution
    if momentum["macd_direction"] == "BULLISH":
        bull_signals += 1
    elif momentum["macd_direction"] == "BEARISH":
        bear_signals += 1

    # Stochastic contribution
    if "BULLISH" in momentum["stochastic_signal"]:
        bull_signals += 1
    elif "BEARISH" in momentum["stochastic_signal"]:
        bear_signals += 1

    # MFI contribution
    if momentum.get("mfi_zone") == "OVERSOLD":
        bull_signals += 1
    elif momentum.get("mfi_zone") == "OVERBOUGHT":
        bear_signals += 1

    total = bull_signals + bear_signals
    if total == 0:
        bias = "NEUTRAL"
        score = 0
    elif bull_signals > bear_signals:
        bias = "BULLISH"
        score = round(bull_signals / max(total, 1) * 100, 1)
    elif bear_signals > bull_signals:
        bias = "BEARISH"
        score = round(bear_signals / max(total, 1) * 100, 1)
    else:
        bias = "NEUTRAL"
        score = 50.0

    return {
        "bias": bias,
        "score": score,
        "bull_signals": bull_signals,
        "bear_signals": bear_signals,
        "total_signals": total,
    }


def build_timeframe_summary(
    closes: List[float],
    highs: List[float],
    lows: List[float],
    volumes: List[float],
    timeframe_name: str,
) -> Dict[str, Any]:
    """Construit le résumé sémantique pour un timeframe donné."""
    if not closes or len(closes) < 30:
        return {"timeframe": timeframe_name, "error": "Données insuffisantes"}

    price = closes[0]

    # Indicateurs corrigés
    ema_9 = ind.ema(closes, 9) or price
    ema_21 = ind.ema(closes, 21) or price
    ema_50 = ind.ema(closes, 50) or price

    rsi = ind.rsi_wilder(closes, 14) or 50.0

    macd_data = ind.macd(closes)
    macd_hist = macd_data.get("histogram", 0) or 0

    atr = ind.atr(highs, lows, closes, 14) or 0
    bb = ind.bollinger(closes, 20, 2.0)
    bb_upper = bb.get("upper", price) or price
    bb_lower = bb.get("lower", price) or price
    bb_mid = bb.get("middle", price) or price

    stoch = ind.stochastic(highs, lows, closes, 14, 3)
    stoch_k = stoch.get("k", 50) or 50
    stoch_d = stoch.get("d", 50) or 50

    obv = ind.obv(closes, volumes)
    adx_data = ind.adx(highs, lows, closes, 14)

    mfi = None
    if volumes and any(v > 0 for v in volumes[:14]):
        mfi = ind.mfi(highs, lows, closes, volumes, 14)

    # Classifications sémantiques
    trend = classify_trend(ema_9, ema_21, ema_50, price)
    vol_state = classify_volatility(atr, price, bb_upper, bb_lower, bb_mid)
    mom = classify_momentum(rsi, macd_hist, stoch_k, stoch_d, mfi)
    confluence = compute_confluence_score(trend, mom, vol_state)

    # Niveaux clés (scalaires : dernier H/L/C, index 0 = plus récent)
    pivots = ind.pivot_points(highs[0], lows[0], closes[0])
    fib = ind.fibonacci_levels(highs[0], lows[0])

    # Market regime
    adx_val = adx_data.get("adx") if adx_data else None
    regime = ind.detect_market_regime(closes, adx_value=adx_val, atr_value=atr, bb_data=bb)

    # Candle patterns (dernière bougie vs précédente)
    # Note : opens non disponibles → approximation open ≈ close précédent
    if len(closes) >= 2 and len(highs) >= 2 and len(lows) >= 2:
        cur_o = closes[1]   # open courant ≈ close précédent
        cur_h, cur_l, cur_c = highs[0], lows[0], closes[0]
        prev_o = closes[2] if len(closes) >= 3 else closes[1]
        prev_h, prev_l, prev_c = highs[1], lows[1], closes[1]
        patterns = ind.candle_patterns(cur_o, cur_h, cur_l, cur_c,
                                       prev_o, prev_h, prev_l, prev_c)
    else:
        patterns = {}

    return {
        "timeframe": timeframe_name,
        "price": round(price, 6),
        "trend": trend,
        "volatility": vol_state,
        "momentum": mom,
        "confluence": confluence,
        "atr": round(atr, 6),
        "adx": adx_data,
        "obv_direction": "UP" if obv and obv > 0 else "DOWN" if obv and obv < 0 else "FLAT",
        "key_levels": {
            "pivot": pivots,
            "fibonacci": fib,
        },
        "market_regime": regime,
        "candle_patterns": patterns,
    }


def build_smart_payload(
    symbol: str,
    timeframes_data: Dict[str, Dict[str, List[float]]],
    risk_state: Dict[str, Any],
    open_positions: List[Dict[str, Any]],
    context: str = "entry",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Construit le payload intelligent pour l'IA.

    Args:
        symbol: Paire de trading (ex: BTCUSD)
        timeframes_data: dict { "M1": {"close": [...], "high": [...], "low": [...], "volume": [...]}, ... }
        risk_state: État du risk guardian
        open_positions: Positions ouvertes actuelles
        context: "entry" ou "exit"
        extra: Données supplémentaires

    Returns:
        Payload structuré et compressé sémantiquement.
    """
    summaries = {}
    for tf_name, tf_data in timeframes_data.items():
        closes = tf_data.get("close", [])
        highs = tf_data.get("high", [])
        lows = tf_data.get("low", [])
        volumes = tf_data.get("volume", [])

        summaries[tf_name] = build_timeframe_summary(
            closes, highs, lows, volumes, tf_name,
        )

    # Multi-timeframe synthesis
    mtf_synthesis = _synthesize_mtf(summaries)

    payload = {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "context": context,
        "multi_timeframe": summaries,
        "mtf_synthesis": mtf_synthesis,
        "risk_state": risk_state,
        "open_positions": [
            {
                "ticket": p.get("ticket"),
                "type": p.get("type"),
                "volume": p.get("volume"),
                "price_open": p.get("price_open"),
                "sl": p.get("sl"),
                "tp": p.get("tp"),
                "profit": p.get("profit"),
                "time_open": p.get("time_open"),
            }
            for p in open_positions
        ],
    }

    if extra:
        payload["extra"] = extra

    return payload


def _synthesize_mtf(summaries: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Synthèse multi-timeframe — résumé global."""
    bull = 0
    bear = 0
    neutral = 0
    tf_trends = {}

    for tf_name, s in summaries.items():
        if "error" in s:
            continue
        conf = s.get("confluence", {})
        bias = conf.get("bias", "NEUTRAL")
        tf_trends[tf_name] = bias

        if bias == "BULLISH":
            bull += 1
        elif bias == "BEARISH":
            bear += 1
        else:
            neutral += 1

    total = bull + bear + neutral
    if total == 0:
        overall = "NO_DATA"
    elif bull > bear and bull > neutral:
        overall = "BULLISH"
    elif bear > bull and bear > neutral:
        overall = "BEARISH"
    else:
        overall = "MIXED"

    # Alignement des timeframes
    alignment = "ALIGNED" if (bull == total or bear == total) else "MIXED"

    return {
        "overall_bias": overall,
        "alignment": alignment,
        "timeframe_biases": tf_trends,
        "bullish_count": bull,
        "bearish_count": bear,
        "neutral_count": neutral,
    }


def estimate_token_count(payload: Dict) -> int:
    """Estimation grossière du nombre de tokens du payload."""
    import json
    text = json.dumps(payload)
    # ~4 chars per token en moyenne
    return len(text) // 4
