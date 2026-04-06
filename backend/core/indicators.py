"""
INDICATEURS TECHNIQUES — Implémentations correctes (standards industriels)
ForexBot SaaS — Module partagé pour tous les composants.

Convention données : index 0 = valeur la plus récente (après [::-1] sur MT5).
Toutes les fonctions gèrent en interne la conversion vers l'ordre chronologique
quand le calcul l'exige (EMA, RSI Wilder, MACD, ADX…).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, cast
import math


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════

def _to_chrono(values: List[float]) -> List[float]:
    """Reverse list so index 0 = oldest (chronological order)."""
    return list(reversed(values))


# ═══════════════════════════════════════════════════════════════
#  EMA — Exponential Moving Average (standard)
# ═══════════════════════════════════════════════════════════════

def ema(values: List[float], period: int) -> Optional[float]:
    """
    EMA correcte calculée du passé vers le présent.
    Seed = SMA des `period` premières valeurs chronologiques.
    Retourne la valeur EMA la plus récente.
    """
    if len(values) < period:
        return None
    c = _to_chrono(values)
    k = 2.0 / (period + 1)
    ema_val = sum(c[:period]) / period  # SMA seed
    for v in c[period:]:
        ema_val = v * k + ema_val * (1 - k)
    return ema_val


def ema_series(values: List[float], period: int) -> List[float]:
    """
    Retourne la série EMA complète (en ordre chronologique).
    Utile pour MACD signal line.
    """
    if len(values) < period:
        return []
    c = _to_chrono(values)
    k = 2.0 / (period + 1)
    result: list[float] = []
    ema_val = sum(c[:period]) / period
    result.append(ema_val)
    for v in c[period:]:
        ema_val = v * k + ema_val * (1 - k)
        result.append(ema_val)
    return result


# ═══════════════════════════════════════════════════════════════
#  SMA — Simple Moving Average
# ═══════════════════════════════════════════════════════════════

def sma(values: List[float], period: int) -> Optional[float]:
    """SMA sur les `period` valeurs les plus récentes."""
    if len(values) < period:
        return None
    return sum(values[:period]) / period


# ═══════════════════════════════════════════════════════════════
#  RSI — Wilder's Smoothing (standard industriel)
# ═══════════════════════════════════════════════════════════════

def rsi_wilder(values: List[float], period: int = 14) -> Optional[float]:
    """
    RSI de Wilder avec lissage exponentiel.
    1. Calcul initial avg_gain / avg_loss sur `period` barres (SMA).
    2. Lissage Wilder : avg = (prev_avg * (period-1) + current) / period.
    """
    c = _to_chrono(values)
    if len(c) <= period:
        return None

    deltas = [c[i] - c[i - 1] for i in range(1, len(c))]

    # Phase initiale : SMA
    gains_init = [max(d, 0.0) for d in deltas[:period]]
    losses_init = [max(-d, 0.0) for d in deltas[:period]]
    avg_gain = sum(gains_init) / period
    avg_loss = sum(losses_init) / period

    # Phase Wilder : lissage exponentiel
    for i in range(period, len(deltas)):
        d = deltas[i]
        avg_gain = (avg_gain * (period - 1) + max(d, 0.0)) / period
        avg_loss = (avg_loss * (period - 1) + max(-d, 0.0)) / period

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 4)


# ═══════════════════════════════════════════════════════════════
#  MACD — Moving Average Convergence Divergence (complet)
# ═══════════════════════════════════════════════════════════════

def macd(
    values: List[float],
    fast: int = 12,
    slow: int = 26,
    signal_period: int = 9,
) -> Dict[str, Optional[float]]:
    """
    MACD complet :
      macd_line  = EMA(fast) - EMA(slow)
      signal     = EMA(signal_period) de la série MACD
      histogram  = macd_line - signal
    """
    c = _to_chrono(values)
    need = slow + signal_period
    if len(c) < need:
        return {"macd": None, "signal": None, "hist": None}

    k_fast = 2.0 / (fast + 1)
    k_slow = 2.0 / (slow + 1)

    # Build EMA-fast and EMA-slow series from index `slow-1`
    ema_f = sum(c[:fast]) / fast
    ema_s = sum(c[:slow]) / slow

    # Advance EMA-fast to index slow-1
    for i in range(fast, slow):
        ema_f = c[i] * k_fast + ema_f * (1 - k_fast)

    macd_series: List[float] = []
    macd_series.append(ema_f - ema_s)

    for i in range(slow, len(c)):
        ema_f = c[i] * k_fast + ema_f * (1 - k_fast)
        ema_s = c[i] * k_slow + ema_s * (1 - k_slow)
        macd_series.append(ema_f - ema_s)

    if len(macd_series) < signal_period:
        return {"macd": macd_series[-1] if macd_series else None, "signal": None, "hist": None}

    # Signal line = EMA of MACD series
    k_sig = 2.0 / (signal_period + 1)
    sig = sum(macd_series[:signal_period]) / signal_period
    for v in macd_series[signal_period:]:
        sig = v * k_sig + sig * (1 - k_sig)

    macd_val = macd_series[-1]
    hist = macd_val - sig
    return {"macd": round(macd_val, 6), "signal": round(sig, 6), "hist": round(hist, 6)}


# ═══════════════════════════════════════════════════════════════
#  ATR — Average True Range (Wilder)
# ═══════════════════════════════════════════════════════════════

def atr(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 14,
) -> Optional[float]:
    """
    ATR de Wilder.
    Les listes sont index 0 = plus récent.
    On convertit en chronologique pour le calcul.
    """
    h = _to_chrono(highs)
    l = _to_chrono(lows)
    c = _to_chrono(closes)
    if len(c) <= period:
        return None

    # True Range series (from index 1)
    tr_list: List[float] = []
    for i in range(1, len(c)):
        tr = max(
            h[i] - l[i],
            abs(h[i] - c[i - 1]),
            abs(l[i] - c[i - 1]),
        )
        tr_list.append(tr)

    if len(tr_list) < period:
        return None

    # Initial ATR = SMA of first `period` TR values
    atr_val = sum(tr_list[:period]) / period

    # Wilder smoothing
    for i in range(period, len(tr_list)):
        atr_val = (atr_val * (period - 1) + tr_list[i]) / period

    return round(atr_val, 6)


# ═══════════════════════════════════════════════════════════════
#  ADX — Average Directional Index (Wilder, complet)
# ═══════════════════════════════════════════════════════════════

def adx(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    period: int = 14,
) -> Optional[Dict[str, Optional[float]]]:
    """
    ADX complet avec lissage Wilder.
    Retourne : {"adx": float, "plus_di": float, "minus_di": float}
    """
    h = _to_chrono(highs)
    l = _to_chrono(lows)
    c = _to_chrono(closes)
    n = len(c)
    if n <= period + period:  # Need 2*period minimum
        return None

    # Calculate TR, +DM, -DM series
    tr_list: List[float] = []
    plus_dm: List[float] = []
    minus_dm: List[float] = []

    for i in range(1, n):
        tr = max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1]))
        tr_list.append(tr)

        up_move = h[i] - h[i - 1]
        down_move = l[i - 1] - l[i]

        if up_move > down_move and up_move > 0:
            plus_dm.append(up_move)
        else:
            plus_dm.append(0.0)

        if down_move > up_move and down_move > 0:
            minus_dm.append(down_move)
        else:
            minus_dm.append(0.0)

    if len(tr_list) < period:
        return None

    # Wilder smoothed TR, +DM, -DM
    smoothed_tr = sum(tr_list[:period])
    smoothed_plus = sum(plus_dm[:period])
    smoothed_minus = sum(minus_dm[:period])

    dx_series: List[float] = []

    for i in range(period, len(tr_list)):
        smoothed_tr = smoothed_tr - (smoothed_tr / period) + tr_list[i]
        smoothed_plus = smoothed_plus - (smoothed_plus / period) + plus_dm[i]
        smoothed_minus = smoothed_minus - (smoothed_minus / period) + minus_dm[i]

        if smoothed_tr == 0:
            continue
        pdi = 100.0 * smoothed_plus / smoothed_tr
        mdi = 100.0 * smoothed_minus / smoothed_tr
        denom = pdi + mdi
        if denom == 0:
            dx_series.append(0.0)
        else:
            dx_series.append(abs(pdi - mdi) / denom * 100.0)

    if len(dx_series) < period:
        return None

    # ADX = Wilder smoothed DX
    adx_val = sum(dx_series[:period]) / period
    for i in range(period, len(dx_series)):
        adx_val = (adx_val * (period - 1) + dx_series[i]) / period

    # Final +DI / -DI
    if smoothed_tr == 0:
        pdi_final = 0.0
        mdi_final = 0.0
    else:
        pdi_final = 100.0 * smoothed_plus / smoothed_tr
        mdi_final = 100.0 * smoothed_minus / smoothed_tr

    return {
        "adx": round(adx_val, 4),
        "plus_di": round(pdi_final, 4),
        "minus_di": round(mdi_final, 4),
    }


# ═══════════════════════════════════════════════════════════════
#  Bollinger Bands (sample std)
# ═══════════════════════════════════════════════════════════════

def bollinger(
    values: List[float], period: int = 20, std_mult: float = 2.0
) -> Dict[str, Optional[float]]:
    """Bollinger Bands avec écart-type d'échantillon (N-1)."""
    if len(values) < period:
        return {"mid": None, "upper": None, "lower": None}
    window = values[:period]
    mean = sum(window) / period
    variance = sum((v - mean) ** 2 for v in window) / (period - 1)  # Sample std
    std = math.sqrt(variance)
    return {
        "mid": round(mean, 6),
        "upper": round(mean + std_mult * std, 6),
        "lower": round(mean - std_mult * std, 6),
    }


# ═══════════════════════════════════════════════════════════════
#  Stochastic (%K + %D)
# ═══════════════════════════════════════════════════════════════

def stochastic(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    k_period: int = 14,
    d_period: int = 3,
) -> Dict[str, Optional[float]]:
    """Stochastic Oscillator avec %K et %D (SMA of %K)."""
    if len(closes) < k_period + d_period - 1:
        return {"k": None, "d": None}

    k_values: List[float] = []
    for offset in range(d_period):
        start = offset
        end = start + k_period
        if end > len(highs):
            break
        highest = max(highs[start:end])
        lowest = min(lows[start:end])
        if highest == lowest:
            k_values.append(50.0)
        else:
            k_values.append((closes[start] - lowest) / (highest - lowest) * 100.0)

    if not k_values:
        return {"k": None, "d": None}

    k_val = k_values[0]
    d_val = sum(k_values) / len(k_values) if len(k_values) >= d_period else k_val
    return {"k": round(k_val, 4), "d": round(d_val, 4)}


# ═══════════════════════════════════════════════════════════════
#  OBV — On-Balance Volume (ordre chronologique correct)
# ═══════════════════════════════════════════════════════════════

def obv(closes: List[float], volumes: List[float], period: int = 20) -> Optional[float]:
    """
    OBV calculé dans l'ordre chronologique correct.
    Si prix monte → +volume, si prix baisse → -volume.
    """
    c = _to_chrono(closes)
    v = _to_chrono(volumes)
    if len(c) <= period:
        return None

    start = max(0, len(c) - period - 1)
    obv_val = 0.0
    for i in range(start + 1, len(c)):
        if c[i] > c[i - 1]:
            obv_val += v[i]
        elif c[i] < c[i - 1]:
            obv_val -= v[i]
    return obv_val


# ═══════════════════════════════════════════════════════════════
#  MFI — Money Flow Index (ordre chronologique correct)
# ═══════════════════════════════════════════════════════════════

def mfi(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: List[float],
    period: int = 14,
) -> Optional[float]:
    """MFI calculé en ordre chronologique correct."""
    h = _to_chrono(highs)
    l = _to_chrono(lows)
    c = _to_chrono(closes)
    v = _to_chrono(volumes)
    if len(c) <= period:
        return None

    start = max(0, len(c) - period - 1)
    pos_flow = 0.0
    neg_flow = 0.0
    for i in range(start + 1, len(c)):
        tp_curr = (h[i] + l[i] + c[i]) / 3.0
        tp_prev = (h[i - 1] + l[i - 1] + c[i - 1]) / 3.0
        flow = tp_curr * v[i]
        if tp_curr > tp_prev:
            pos_flow += flow
        elif tp_curr < tp_prev:
            neg_flow += flow

    if neg_flow == 0:
        return 100.0
    mr = pos_flow / neg_flow
    return round(100.0 - (100.0 / (1.0 + mr)), 4)


# ═══════════════════════════════════════════════════════════════
#  CCI — Commodity Channel Index
# ═══════════════════════════════════════════════════════════════

def cci(
    highs: List[float], lows: List[float], closes: List[float], period: int = 20
) -> Optional[float]:
    """CCI standard."""
    if len(closes) < period:
        return None
    typical = [(highs[i] + lows[i] + closes[i]) / 3.0 for i in range(period)]
    mean = sum(typical) / period
    mean_dev = sum(abs(t - mean) for t in typical) / period
    if mean_dev == 0:
        return 0.0
    return round((typical[0] - mean) / (0.015 * mean_dev), 4)


# ═══════════════════════════════════════════════════════════════
#  ROC — Rate Of Change
# ═══════════════════════════════════════════════════════════════

def roc(values: List[float], period: int = 12) -> Optional[float]:
    """ROC = (current - past) / past * 100."""
    if len(values) <= period:
        return None
    prev = values[period]
    if prev == 0:
        return None
    return round((values[0] - prev) / prev * 100.0, 4)


# ═══════════════════════════════════════════════════════════════
#  VWAP — Volume Weighted Average Price
# ═══════════════════════════════════════════════════════════════

def vwap(
    highs: List[float],
    lows: List[float],
    closes: List[float],
    volumes: List[float],
    period: int = 20,
) -> Optional[float]:
    """VWAP sur les `period` barres les plus récentes."""
    if len(closes) < period:
        return None
    pv = 0.0
    vol_sum = 0.0
    for i in range(period):
        tp = (highs[i] + lows[i] + closes[i]) / 3.0
        pv += tp * volumes[i]
        vol_sum += volumes[i]
    if vol_sum == 0:
        return None
    return round(pv / vol_sum, 6)


# ═══════════════════════════════════════════════════════════════
#  Standard Deviation (sample)
# ═══════════════════════════════════════════════════════════════

def stddev(values: List[float], period: int) -> Optional[float]:
    """Écart-type d'échantillon (N-1)."""
    if len(values) < period:
        return None
    window = values[:period]
    mean = sum(window) / period
    variance = sum((v - mean) ** 2 for v in window) / max(period - 1, 1)
    return round(math.sqrt(variance), 6)


# ═══════════════════════════════════════════════════════════════
#  Slope (linear regression)
# ═══════════════════════════════════════════════════════════════

def slope(values: List[float], period: int = 20) -> Optional[float]:
    """Pente de régression linéaire sur les `period` barres récentes."""
    if len(values) < period:
        return None
    # index 0 = most recent = Y at x=period-1
    n = period
    x_mean = (n - 1) / 2.0
    y = values[:period]
    y_mean = sum(y) / n
    num = sum((i - x_mean) * (y[n - 1 - i] - y_mean) for i in range(n))
    den = sum((i - x_mean) ** 2 for i in range(n))
    if den == 0:
        return None
    return round(num / den, 8)


# ═══════════════════════════════════════════════════════════════
#  Momentum
# ═══════════════════════════════════════════════════════════════

def momentum(values: List[float], period: int = 10) -> Optional[float]:
    """Momentum = current - past."""
    if len(values) <= period:
        return None
    return values[0] - values[period]


# ═══════════════════════════════════════════════════════════════
#  Candle features & patterns
# ═══════════════════════════════════════════════════════════════

def candle_features(o: float, h: float, l: float, c: float) -> Dict[str, float]:
    """Body, upper wick, lower wick, direction."""
    body = abs(c - o)
    upper = max(0.0, h - max(o, c))
    lower = max(0.0, min(o, c) - l)
    direction = 1 if c > o else (-1 if c < o else 0)
    rng = max(h - l, 1e-10)
    return {
        "body": body,
        "body_ratio": body / rng,
        "upper_wick": upper,
        "lower_wick": lower,
        "direction": direction,
        "range": rng,
    }


def candle_patterns(
    o: float, h: float, l: float, c: float,
    prev_o: float, prev_h: float, prev_l: float, prev_c: float,
) -> Dict[str, bool]:
    """Détection de patterns de chandeliers japonais."""
    body = abs(c - o)
    rng = max(1e-10, h - l)
    upper = max(0.0, h - max(o, c))
    lower = max(0.0, min(o, c) - l)

    is_doji = body <= rng * 0.1
    is_pin_bar = (upper >= body * 2 and lower <= body * 0.5) or (
        lower >= body * 2 and upper <= body * 0.5
    )
    bullish_engulfing = prev_c < prev_o and c > o and c >= prev_o and o <= prev_c
    bearish_engulfing = prev_c > prev_o and c < o and o >= prev_c and c <= prev_o
    hammer = lower >= body * 2 and upper <= body * 0.5 and c >= o
    shooting_star = upper >= body * 2 and lower <= body * 0.5 and c <= o
    inside_bar = h <= prev_h and l >= prev_l
    bullish_harami = prev_c < prev_o and c > o and c <= prev_o and o >= prev_c
    bearish_harami = prev_c > prev_o and c < o and o <= prev_c and c >= prev_o
    marubozu = upper <= rng * 0.05 and lower <= rng * 0.05 and body >= rng * 0.7
    long_wick_reversal = (upper >= rng * 0.6) or (lower >= rng * 0.6)

    return {
        "doji": bool(is_doji),
        "pin_bar": bool(is_pin_bar),
        "bullish_engulfing": bool(bullish_engulfing),
        "bearish_engulfing": bool(bearish_engulfing),
        "hammer": bool(hammer),
        "shooting_star": bool(shooting_star),
        "inside_bar": bool(inside_bar),
        "bullish_harami": bool(bullish_harami),
        "bearish_harami": bool(bearish_harami),
        "marubozu": bool(marubozu),
        "long_wick_reversal": bool(long_wick_reversal),
    }


# ═══════════════════════════════════════════════════════════════
#  Support & Resistance (pivot points + dynamic S&R)
# ═══════════════════════════════════════════════════════════════

def pivot_points(
    high: float, low: float, close: float
) -> Dict[str, float]:
    """Pivot points classiques (floor method)."""
    pivot = (high + low + close) / 3.0
    return {
        "pivot": round(pivot, 6),
        "s1": round(2 * pivot - high, 6),
        "s2": round(pivot - (high - low), 6),
        "s3": round(low - 2 * (high - pivot), 6),
        "r1": round(2 * pivot - low, 6),
        "r2": round(pivot + (high - low), 6),
        "r3": round(high + 2 * (pivot - low), 6),
    }


def fibonacci_levels(
    high: float, low: float, direction: str = "up"
) -> Dict[str, float]:
    """Niveaux de retracement Fibonacci."""
    diff = high - low
    levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
    result: Dict[str, float] = {}
    for lvl in levels:
        key = f"fib_{lvl:.3f}"
        if direction == "up":
            result[key] = round(high - diff * lvl, 6)
        else:
            result[key] = round(low + diff * lvl, 6)
    return result


# ═══════════════════════════════════════════════════════════════
#  Market regime detection
# ═══════════════════════════════════════════════════════════════

def detect_market_regime(
    closes: List[float],
    adx_value: Optional[float] = None,
    atr_value: Optional[float] = None,
    bb_data: Optional[Dict[str, Optional[float]]] = None,
) -> str:
    """
    Détecte le régime de marché :
      TRENDING_UP, TRENDING_DOWN, RANGING, HIGH_VOLATILITY, LOW_VOLATILITY
    """
    if len(closes) < 50:
        return "UNKNOWN"

    sma_20 = sum(closes[:20]) / 20
    sma_50 = sum(closes[:50]) / 50
    price = closes[0]

    # ADX-based
    if adx_value is not None:
        if adx_value > 25:
            if price > sma_20 > sma_50:
                return "TRENDING_UP"
            elif price < sma_20 < sma_50:
                return "TRENDING_DOWN"
            else:
                return "TRENDING_MIXED"
        elif adx_value < 20:
            return "RANGING"

    # Fallback: price position
    if price > sma_20 > sma_50:
        return "TRENDING_UP"
    elif price < sma_20 < sma_50:
        return "TRENDING_DOWN"

    # Bollinger width
    if bb_data and bb_data.get("upper") and bb_data.get("lower") and bb_data.get("mid"):
        upper = bb_data["upper"]
        lower = bb_data["lower"]
        mid = bb_data["mid"]
        if upper is not None and lower is not None and mid is not None and mid != 0:
            bb_width = (upper - lower) / mid
            if bb_width > 0.04:
                return "HIGH_VOLATILITY"
            elif bb_width < 0.01:
                return "LOW_VOLATILITY"

    return "RANGING"


# ═══════════════════════════════════════════════════════════════
#  Confluence scoring
# ═══════════════════════════════════════════════════════════════

def confluence_score(indicators: Dict[str, Any]) -> Dict[str, float]:
    """
    Score de confluence multi-indicateurs.
    Retourne un score bullish et bearish entre 0 et 1.
    """
    bullish = 0.0
    bearish = 0.0
    count = 0

    # RSI
    rsi_val = indicators.get("rsi_14")
    if rsi_val is not None:
        count += 1
        if rsi_val < 30:
            bullish += 1.0
        elif rsi_val < 40:
            bullish += 0.5
        elif rsi_val > 70:
            bearish += 1.0
        elif rsi_val > 60:
            bearish += 0.5

    # MACD
    _macd_raw = indicators.get("macd")
    if isinstance(_macd_raw, dict):
        macd_data = cast(Dict[str, Any], _macd_raw)
        if macd_data.get("hist") is not None:
            count += 1
            if macd_data["hist"] > 0:
                bullish += 0.8
            else:
                bearish += 0.8

    # EMA cross
    ema_fast = indicators.get("ema_9")
    ema_slow = indicators.get("ema_21")
    if ema_fast is not None and ema_slow is not None:
        count += 1
        if ema_fast > ema_slow:
            bullish += 0.7
        else:
            bearish += 0.7

    # Stochastic
    _stoch_raw = indicators.get("stoch")
    if isinstance(_stoch_raw, dict):
        stoch = cast(Dict[str, Any], _stoch_raw)
        if stoch.get("k") is not None:
            count += 1
            if stoch["k"] < 20:
                bullish += 0.6
            elif stoch["k"] > 80:
                bearish += 0.6

    # ADX trend
    _adx_raw = indicators.get("adx_14")
    if isinstance(_adx_raw, dict):
        adx_data = cast(Dict[str, Any], _adx_raw)
        if adx_data.get("adx") is not None:
            if adx_data["adx"] > 25:
                count += 1
                if adx_data.get("plus_di", 0) > adx_data.get("minus_di", 0):
                    bullish += 0.9
                else:
                    bearish += 0.9

    total = max(count, 1)
    return {
        "bullish": round(bullish / total, 4),
        "bearish": round(bearish / total, 4),
        "signal_count": count,
    }
