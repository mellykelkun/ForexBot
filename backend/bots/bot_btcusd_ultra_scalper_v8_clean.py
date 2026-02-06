"""
BTCUSD MICRO SCALPER V8 PRO - Version stable (IA uniquement)
Décision d'entrée/sortie via /api/decision (Groq)
"""

import argparse
import hashlib
import json
import logging
import os
import shutil
import time
from decimal import Decimal, ROUND_DOWN
from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import MetaTrader5 as mt5
import requests
from requests import exceptions as req_exc

from backend.config.config_micro_scalping_pro import (
    SYMBOLS_CONFIG,
    MICRO_SCALPING_CONFIG,
    SECURITY_CONFIG,
)


AI_DECISION_URL = os.getenv("AI_ENGINE_URL", "http://127.0.0.1:5003/api/decision")
AI_HEALTH_URL = os.getenv("AI_ENGINE_HEALTH_URL", "http://127.0.0.1:5003/health")

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


DEFAULT_RISK = {
    "max_trades_per_hour": _env_int("MAX_TRADES_PER_HOUR", 6),
    "max_trades_per_day": _env_int("MAX_TRADES_PER_DAY", 60),
    "min_seconds_between_trades": _env_int("MIN_SECONDS_BETWEEN_TRADES", 15),
    "max_daily_loss_pct": _env_float("MAX_DAILY_LOSS_PCT", 2.0),
    "max_slippage_points": _env_float("MAX_SLIPPAGE_POINTS", 25),
    "max_latency_ms": _env_int("MAX_LATENCY_MS", 800),
    "commission_per_lot": _env_float("COMMISSION_PER_LOT", 0.0),
    "simulated_slippage_points": _env_float("SIMULATED_SLIPPAGE_POINTS", 5),
}

DEFAULT_GUARD = {
    "ai_error_limit": 5,
    "ai_cooldown_seconds": 120,
    "backup_interval_seconds": 600,
}


class TradeJournal:
    def __init__(self, log_path: str = "logs/trade_journal.jsonl"):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        self.last_hash = self._load_last_hash()

    def _load_last_hash(self) -> str:
        if not os.path.exists(self.log_path):
            return ""
        try:
            with open(self.log_path, "rb") as f:
                lines = f.read().splitlines()
                if not lines:
                    return ""
                last = json.loads(lines[-1].decode("utf-8"))
                return last.get("hash", "")
        except Exception:
            return ""

    def log_event(self, event: Dict[str, Any]):
        payload = {"timestamp": datetime.utcnow().isoformat(), **event, "prev_hash": self.last_hash}
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        payload["hash"] = digest
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.last_hash = digest


class RiskManager:
    def __init__(self, starting_balance: float, risk_cfg: Dict[str, Any]):
        self.starting_balance = starting_balance
        self.cfg = {**DEFAULT_RISK, **(risk_cfg or {})}
        self.trade_times = deque(maxlen=1000)
        self.last_trade_time: Optional[datetime] = None

    def _prune(self, now: datetime):
        while self.trade_times and (now - self.trade_times[0]).total_seconds() > 24 * 3600:
            self.trade_times.popleft()

    def can_trade(self, now: datetime, current_balance: float) -> (bool, str):
        self._prune(now)

        if self.last_trade_time:
            dt = (now - self.last_trade_time).total_seconds()
            if dt < self.cfg["min_seconds_between_trades"]:
                return False, f"Anti-sur-trading: {dt:.1f}s < {self.cfg['min_seconds_between_trades']}s"

        trades_last_hour = [t for t in self.trade_times if (now - t).total_seconds() <= 3600]
        if len(trades_last_hour) >= self.cfg["max_trades_per_hour"]:
            return False, "Limite trades/heure atteinte"

        if len(self.trade_times) >= self.cfg["max_trades_per_day"]:
            return False, "Limite trades/jour atteinte"

        max_loss = -abs(self.starting_balance) * (self.cfg["max_daily_loss_pct"] / 100.0)
        pnl = current_balance - self.starting_balance
        if pnl <= max_loss:
            return False, "Limite de perte journalière atteinte"

        return True, "OK"

    def record_trade(self, when: datetime):
        self.trade_times.append(when)
        self.last_trade_time = when

    def get_stats(self, now: datetime) -> Dict[str, Any]:
        self._prune(now)
        trades_last_hour = sum(1 for t in self.trade_times if (now - t).total_seconds() <= 3600)
        trades_last_day = len(self.trade_times)
        last_trade_seconds_ago = None
        if self.last_trade_time:
            last_trade_seconds_ago = (now - self.last_trade_time).total_seconds()
        return {
            "trades_last_hour": trades_last_hour,
            "trades_last_day": trades_last_day,
            "last_trade_seconds_ago": last_trade_seconds_ago,
        }


class BTCUSDMicroScalperPro:
    def __init__(self):
        self.real_trading = False
        self.account = None
        self.active_symbols = [s for s, cfg in SYMBOLS_CONFIG.items() if cfg.get("enabled")]
        self.request_timeout = SECURITY_CONFIG.get("request_timeout", 5)
        self.last_trade_time: Optional[datetime] = None
        self.last_ai_decision: Optional[Dict[str, Any]] = None
        self.last_ai_error: Optional[str] = None
        self.last_ai_time: Optional[datetime] = None
        self.ai_error_streak = 0
        self.ai_cooldown_until: Optional[datetime] = None
        self.journal = TradeJournal()
        self.risk_manager: Optional[RiskManager] = None
        self.daily_start_balance: Optional[float] = None
        self.daily_start_date: Optional[str] = None
        self.hard_stop_triggered = False
        self.backup_last_run: Optional[datetime] = None
        self.dormant_after_minutes = 30
        self.dormant_check_seconds = 60
        self.dormant_sleep_seconds = 15
        self.is_dormant = False
        default_cooldown = MICRO_SCALPING_CONFIG.get("cooldown_seconds", 6)
        self.decision_interval_seconds = max(8, _env_int("DECISION_INTERVAL_SECONDS", default_cooldown))
        self.required_confidence = _env_float("REQUIRED_CONFIDENCE", MICRO_SCALPING_CONFIG.get("required_confidence", 0.6))
        self.max_spread_points = _env_float("MAX_SPREAD_POINTS", 100.0)
        self.log_purge_interval_minutes = int(os.getenv("LOG_PURGE_INTERVAL_MINUTES", "720"))
        self.log_purge_max_size_mb = float(os.getenv("LOG_PURGE_MAX_MB", "50"))
        self.log_purge_last_run: Optional[datetime] = None

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
        self.risk_manager = RiskManager(self.account.balance, {})
        self.daily_start_balance = self.account.balance
        self.daily_start_date = datetime.now().strftime("%Y-%m-%d")
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

    def _ema(self, values, period: int) -> Optional[float]:
        if len(values) < period:
            return None
        k = 2 / (period + 1)
        ema = values[0]
        for v in values[1:]:
            ema = v * k + ema * (1 - k)
        return ema

    def _rsi(self, values, period: int = 14) -> Optional[float]:
        if len(values) <= period:
            return None
        gains = 0.0
        losses = 0.0
        for i in range(1, period + 1):
            diff = values[i] - values[i - 1]
            if diff >= 0:
                gains += diff
            else:
                losses -= diff
        avg_gain = gains / period
        avg_loss = losses / period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _sma(self, values, period: int) -> Optional[float]:
        if len(values) < period:
            return None
        return sum(values[:period]) / period

    def _roc(self, values, period: int = 12) -> Optional[float]:
        if len(values) <= period:
            return None
        prev = values[period]
        if prev == 0:
            return None
        return (values[0] - prev) / prev * 100

    def _cci(self, highs, lows, closes, period: int = 20) -> Optional[float]:
        if len(closes) < period:
            return None
        typical = [(highs[i] + lows[i] + closes[i]) / 3 for i in range(period)]
        sma = sum(typical) / period
        mean_dev = sum(abs(t - sma) for t in typical) / period
        if mean_dev == 0:
            return None
        return (typical[0] - sma) / (0.015 * mean_dev)

    def _obv(self, closes, volumes, period: int = 20) -> Optional[float]:
        if len(closes) <= period:
            return None
        obv = 0.0
        for i in range(1, period + 1):
            if closes[i - 1] > closes[i]:
                obv += volumes[i - 1]
            elif closes[i - 1] < closes[i]:
                obv -= volumes[i - 1]
        return obv

    def _mfi(self, highs, lows, closes, volumes, period: int = 14) -> Optional[float]:
        if len(closes) <= period:
            return None
        pos_flow = 0.0
        neg_flow = 0.0
        for i in range(1, period + 1):
            tp_curr = (highs[i - 1] + lows[i - 1] + closes[i - 1]) / 3
            tp_prev = (highs[i] + lows[i] + closes[i]) / 3
            flow = tp_curr * volumes[i - 1]
            if tp_curr > tp_prev:
                pos_flow += flow
            elif tp_curr < tp_prev:
                neg_flow += flow
        if neg_flow == 0:
            return 100.0
        mr = pos_flow / neg_flow
        return 100 - (100 / (1 + mr))

    def _adx(self, highs, lows, closes, period: int = 14) -> Optional[float]:
        if len(closes) <= period:
            return None
        tr_list = []
        plus_dm = []
        minus_dm = []
        for i in range(1, period + 1):
            tr = max(
                highs[i - 1] - lows[i - 1],
                abs(highs[i - 1] - closes[i]),
                abs(lows[i - 1] - closes[i]),
            )
            tr_list.append(tr)
            up_move = highs[i - 1] - highs[i]
            down_move = lows[i] - lows[i - 1]
            plus_dm.append(max(up_move, 0.0) if up_move > down_move else 0.0)
            minus_dm.append(max(down_move, 0.0) if down_move > up_move else 0.0)

        tr_sum = sum(tr_list)
        if tr_sum == 0:
            return None
        plus_di = 100 * (sum(plus_dm) / tr_sum)
        minus_di = 100 * (sum(minus_dm) / tr_sum)
        denom = plus_di + minus_di
        if denom == 0:
            return None
        dx = abs(plus_di - minus_di) / denom * 100
        return dx

    def _atr(self, highs, lows, closes, period: int = 14) -> Optional[float]:
        if len(closes) <= period:
            return None
        trs = []
        for i in range(1, period + 1):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            trs.append(tr)
        return sum(trs) / period if trs else None

    def _macd(self, values, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, Optional[float]]:
        if len(values) < slow + signal:
            return {"macd": None, "signal": None, "hist": None}
        ema_fast = self._ema(values, fast)
        ema_slow = self._ema(values, slow)
        if ema_fast is None or ema_slow is None:
            return {"macd": None, "signal": None, "hist": None}
        macd_line = ema_fast - ema_slow
        signal_line = macd_line
        hist = macd_line - signal_line if signal_line is not None else None
        return {"macd": macd_line, "signal": signal_line, "hist": hist}

    def _stochastic(self, highs, lows, closes, k_period: int = 14) -> Optional[float]:
        if len(closes) < k_period:
            return None
        highest = max(highs[:k_period])
        lowest = min(lows[:k_period])
        if highest == lowest:
            return None
        return (closes[0] - lowest) / (highest - lowest) * 100

    def _bollinger(self, values, period: int = 20, std_mult: float = 2.0) -> Dict[str, Optional[float]]:
        if len(values) < period:
            return {"mid": None, "upper": None, "lower": None}
        window = values[:period]
        mean = sum(window) / period
        variance = sum((v - mean) ** 2 for v in window) / period
        std = variance ** 0.5
        return {"mid": mean, "upper": mean + std_mult * std, "lower": mean - std_mult * std}

    def _candle_features(self, o, h, l, c) -> Dict[str, float]:
        body = abs(c - o)
        upper = max(0.0, h - max(o, c))
        lower = max(0.0, min(o, c) - l)
        direction = 1 if c > o else (-1 if c < o else 0)
        return {
            "body": body,
            "upper_wick": upper,
            "lower_wick": lower,
            "direction": direction,
        }

    def _candle_patterns(self, o, h, l, c, prev_o, prev_h, prev_l, prev_c) -> Dict[str, bool]:
        body = abs(c - o)
        rng = max(1e-9, h - l)
        upper = max(0.0, h - max(o, c))
        lower = max(0.0, min(o, c) - l)
        prev_body = abs(prev_c - prev_o)

        is_doji = body <= rng * 0.1
        is_pin_bar = (upper >= body * 2 and lower <= body * 0.5) or (lower >= body * 2 and upper <= body * 0.5)

        bullish_engulfing = (
            prev_c < prev_o
            and c > o
            and c >= prev_o
            and o <= prev_c
        )
        bearish_engulfing = (
            prev_c > prev_o
            and c < o
            and o >= prev_c
            and c <= prev_o
        )

        hammer = lower >= body * 2 and upper <= body * 0.5 and c >= o
        shooting_star = upper >= body * 2 and lower <= body * 0.5 and c <= o
        inside_bar = h <= prev_h and l >= prev_l

        return {
            "doji": bool(is_doji),
            "pin_bar": bool(is_pin_bar),
            "bullish_engulfing": bool(bullish_engulfing),
            "bearish_engulfing": bool(bearish_engulfing),
            "hammer": bool(hammer),
            "shooting_star": bool(shooting_star),
            "inside_bar": bool(inside_bar),
        }

    def _compute_indicators(self, symbol: str, timeframe=mt5.TIMEFRAME_M1, bars: int = 120) -> Dict[str, Any]:
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        if rates is None or len(rates) < 30:
            return {}
        closes = [r["close"] for r in rates][::-1]
        highs = [r["high"] for r in rates][::-1]
        lows = [r["low"] for r in rates][::-1]
        opens = [r["open"] for r in rates][::-1]
        volumes = [r["tick_volume"] for r in rates][::-1]

        rsi = self._rsi(closes, 14)
        atr = self._atr(highs, lows, closes, 14)
        ema_fast = self._ema(closes, 9)
        ema_slow = self._ema(closes, 21)
        sma_20 = self._sma(closes, 20)
        sma_50 = self._sma(closes, 50)
        macd = self._macd(closes, 12, 26, 9)
        stoch = self._stochastic(highs, lows, closes, 14)
        bb = self._bollinger(closes, 20, 2.0)
        roc = self._roc(closes, 12)
        cci = self._cci(highs, lows, closes, 20)
        obv = self._obv(closes, volumes, 20)
        mfi = self._mfi(highs, lows, closes, volumes, 14)
        adx = self._adx(highs, lows, closes, 14)

        last_candles = []
        for i in range(min(3, len(closes))):
            last_candles.append(self._candle_features(opens[i], highs[i], lows[i], closes[i]))

        patterns = {}
        if len(closes) >= 2:
            patterns = self._candle_patterns(
                opens[0], highs[0], lows[0], closes[0],
                opens[1], highs[1], lows[1], closes[1],
            )

        return {
            "timeframe": timeframe,
            "rsi_14": rsi,
            "atr_14": atr,
            "ema_9": ema_fast,
            "ema_21": ema_slow,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "macd": macd,
            "stoch_k": stoch,
            "bb": bb,
            "roc_12": roc,
            "cci_20": cci,
            "obv_20": obv,
            "mfi_14": mfi,
            "adx_14": adx,
            "last_candles": last_candles,
            "patterns": patterns,
        }

    def _normalize_volume(self, symbol_info: mt5.SymbolInfo, desired: float) -> Optional[float]:
        if not symbol_info:
            return None

        step = symbol_info.volume_step if symbol_info.volume_step and symbol_info.volume_step > 0 else 0.01
        min_vol = symbol_info.volume_min if symbol_info.volume_min and symbol_info.volume_min > 0 else step
        max_vol = symbol_info.volume_max if symbol_info.volume_max and symbol_info.volume_max > 0 else None

        vol = max(desired, min_vol)
        if max_vol:
            vol = min(vol, max_vol)

        step_dec = Decimal(str(step))
        vol_dec = Decimal(str(vol))
        normalized = (vol_dec / step_dec).to_integral_value(rounding=ROUND_DOWN) * step_dec

        min_dec = Decimal(str(min_vol))
        if normalized < min_dec:
            normalized = min_dec

        if max_vol:
            max_dec = Decimal(str(max_vol))
            if normalized > max_dec:
                normalized = max_dec

        if normalized <= 0:
            return None

        return float(normalized)

    def _build_payload(self, symbol: str) -> Optional[Dict[str, Any]]:
        tick = self._get_symbol_tick(symbol)
        if not tick:
            return None
        symbol_info = mt5.symbol_info(symbol)
        spread_points = None
        if symbol_info and symbol_info.point:
            spread_points = tick["spread"] / symbol_info.point
        trade_state = {}
        if self.risk_manager:
            trade_state = self.risk_manager.get_stats(datetime.now())
        indicators_m1 = self._compute_indicators(symbol, mt5.TIMEFRAME_M1, 180)
        indicators_m5 = self._compute_indicators(symbol, mt5.TIMEFRAME_M5, 180)
        indicators_h1 = self._compute_indicators(symbol, mt5.TIMEFRAME_H1, 300)
        indicators_h4 = self._compute_indicators(symbol, mt5.TIMEFRAME_H4, 300)
        return {
            "context": "entry",
            "symbol": symbol,
            "bid": tick["bid"],
            "ask": tick["ask"],
            "spread": tick["spread"],
            "spread_points": spread_points,
            "volume": tick["volume"],
            "timestamp": datetime.now().isoformat(),
            "risk": MICRO_SCALPING_CONFIG.get("risk_per_trade", 0.5),
            "indicators": {
                "m1": indicators_m1,
                "m5": indicators_m5,
                "h1": indicators_h1,
                "h4": indicators_h4,
            },
            "constraints": {
                "min_seconds_between_trades": DEFAULT_RISK["min_seconds_between_trades"],
                "max_trades_per_hour": DEFAULT_RISK["max_trades_per_hour"],
                "max_trades_per_day": DEFAULT_RISK["max_trades_per_day"],
                "required_confidence": self.required_confidence,
                "cooldown_seconds": self.decision_interval_seconds,
            },
            "trade_state": trade_state,
        }

    def _request_ai_decision(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.post(
                AI_DECISION_URL,
                json=payload,
                timeout=max(self.request_timeout, 10),
            )
            if resp.status_code != 200:
                logging.warning("⚠️ IA indisponible: %s", resp.text)
                self.last_ai_error = resp.text
                self.last_ai_time = datetime.now()
                self.ai_error_streak += 1
                return None
            data = resp.json()
            if not isinstance(data, dict):
                return None
            self.last_ai_decision = data
            self.last_ai_time = datetime.now()
            self.last_ai_error = None
            self.ai_error_streak = 0
            return data
        except req_exc.ReadTimeout:
            try:
                time.sleep(0.5)
                resp = requests.post(
                    AI_DECISION_URL,
                    json=payload,
                    timeout=max(self.request_timeout, 10),
                )
                if resp.status_code != 200:
                    logging.warning("⚠️ IA indisponible: %s", resp.text)
                    self.last_ai_error = resp.text
                    self.last_ai_time = datetime.now()
                    self.ai_error_streak += 1
                    return None
                data = resp.json()
                if not isinstance(data, dict):
                    return None
                self.last_ai_decision = data
                self.last_ai_time = datetime.now()
                self.last_ai_error = None
                self.ai_error_streak = 0
                return data
            except Exception as e:
                logging.warning("⚠️ Erreur IA: %s", e)
                self.last_ai_error = str(e)
                self.last_ai_time = datetime.now()
                self.ai_error_streak += 1
                return None
        except Exception as e:
            logging.warning("⚠️ Erreur IA: %s", e)
            self.last_ai_error = str(e)
            self.last_ai_time = datetime.now()
            self.ai_error_streak += 1
            return None

    def _check_ai_watchdog(self):
        if self.ai_error_streak >= DEFAULT_GUARD["ai_error_limit"]:
            self.ai_cooldown_until = datetime.now() + timedelta(seconds=DEFAULT_GUARD["ai_cooldown_seconds"])
            logging.warning(
                "🛑 Watchdog IA: %s erreurs consécutives, pause %ss",
                self.ai_error_streak,
                DEFAULT_GUARD["ai_cooldown_seconds"],
            )
            self.ai_error_streak = 0

    def _check_daily_hard_stop(self, current_balance: float) -> bool:
        today = datetime.now().strftime("%Y-%m-%d")
        if self.daily_start_date != today:
            self.daily_start_date = today
            self.daily_start_balance = current_balance
            self.hard_stop_triggered = False

        if self.hard_stop_triggered or self.daily_start_balance is None:
            return True if self.hard_stop_triggered else False

        max_loss = -abs(self.daily_start_balance) * (DEFAULT_RISK["max_daily_loss_pct"] / 100.0)
        pnl = current_balance - self.daily_start_balance
        if pnl <= max_loss:
            self.hard_stop_triggered = True
            logging.warning("🛑 HARD STOP journalier: perte %.2f <= %.2f", pnl, max_loss)
            self.journal.log_event({"type": "hard_stop", "pnl": pnl, "limit": max_loss})
            return True
        return False

    def _maybe_backup_logs(self):
        now = datetime.now()
        if self.backup_last_run and (now - self.backup_last_run).total_seconds() < DEFAULT_GUARD["backup_interval_seconds"]:
            return

        backup_root = os.path.join("backups", now.strftime("%Y%m%d"))
        os.makedirs(backup_root, exist_ok=True)

        # Journaux
        if os.path.exists(self.journal.log_path):
            shutil.copy2(self.journal.log_path, os.path.join(backup_root, "trade_journal.jsonl"))

        # Logs applicatifs
        if os.path.isdir("logs"):
            for name in os.listdir("logs"):
                src = os.path.join("logs", name)
                if os.path.isfile(src):
                    shutil.copy2(src, os.path.join(backup_root, name))

        # Logs lanceur
        if os.path.exists("process_manager.log"):
            shutil.copy2("process_manager.log", os.path.join(backup_root, "process_manager.log"))

        self.backup_last_run = now

    def _maybe_purge_logs(self):
        now = datetime.now()
        if self.log_purge_interval_minutes <= 0:
            return
        if self.log_purge_last_run and (now - self.log_purge_last_run).total_seconds() < self.log_purge_interval_minutes * 60:
            return

        def _should_purge(path: str) -> bool:
            if not os.path.exists(path):
                return False
            size_mb = os.path.getsize(path) / (1024 * 1024)
            return size_mb >= self.log_purge_max_size_mb

        def _truncate(path: str):
            try:
                with open(path, "w", encoding="utf-8"):
                    pass
                logging.warning("🧹 Log purgé: %s", path)
            except Exception as exc:
                logging.warning("⚠️ Échec purge log %s: %s", path, exc)

        # Toujours sauvegarder avant purge
        self._maybe_backup_logs()

        if os.path.isdir("logs"):
            for name in os.listdir("logs"):
                if not name.lower().endswith((".log", ".json", ".jsonl")):
                    continue
                path = os.path.join("logs", name)
                if _should_purge(path):
                    _truncate(path)

        if _should_purge("process_manager.log"):
            _truncate("process_manager.log")

        self.log_purge_last_run = now

    def executer_strategie_micro_ia(self) -> Optional[Dict[str, Any]]:
        for symbol in self.active_symbols:
            payload = self._build_payload(symbol)
            if not payload:
                continue
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info and symbol_info.point:
                spread_points = payload["spread"] / symbol_info.point
                max_spread = self.max_spread_points
                if spread_points > max_spread:
                    self.journal.log_event({
                        "type": "blocked",
                        "symbol": symbol,
                        "reason": "spread_too_high",
                        "spread_points": round(spread_points, 1),
                        "max_spread": max_spread,
                    })
                    logging.warning("⚠️ Spread trop élevé %s: %.1f pts > %.1f pts", symbol, spread_points, max_spread)
                    continue
            decision = self._request_ai_decision(payload)
            if not decision:
                continue
            action = decision.get("action")
            confidence = decision.get("confidence")
            if confidence is not None and confidence < self.required_confidence:
                self.journal.log_event({
                    "type": "blocked",
                    "symbol": symbol,
                    "reason": "low_confidence",
                    "confidence": confidence,
                    "required": self.required_confidence,
                })
                logging.info("ℹ️ Signal ignoré (confidence %.2f < %.2f)", confidence, self.required_confidence)
                continue
            if action in ("BUY", "SELL"):
                self.journal.log_event({"type": "decision", "symbol": symbol, "decision": decision})
                decision["symbol"] = symbol
                return decision
        return None

    def executer_trade(self, decision: Dict[str, Any]) -> bool:
        symbol = decision.get("symbol")
        action = decision.get("action")
        if not symbol or action not in ("BUY", "SELL"):
            return False

        if not self.risk_manager:
            return False

        account_info = mt5.account_info()
        balance = account_info.balance if account_info else 0.0
        ok, reason = self.risk_manager.can_trade(datetime.now(), balance)
        if not ok:
            self.journal.log_event({"type": "blocked", "symbol": symbol, "reason": reason})
            logging.warning("⚠️ Trade bloqué: %s", reason)
            return False

        if not self.real_trading:
            logging.info("[SIMU] %s %s", action, symbol)
            return True

        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info or not symbol_info.visible:
            mt5.symbol_select(symbol, True)
            symbol_info = mt5.symbol_info(symbol)

        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return False

        desired_volume = SYMBOLS_CONFIG.get(symbol, {}).get("min_lot", 0.01)
        volume = self._normalize_volume(symbol_info, desired_volume)
        if volume is None:
            logging.error("❌ Volume invalide pour %s (demandé=%.6f)", symbol, desired_volume)
            self.journal.log_event({
                "type": "order_rejected",
                "symbol": symbol,
                "action": action,
                "reason": "invalid_volume",
                "requested_volume": desired_volume,
            })
            return False
        if abs(volume - desired_volume) > 1e-9:
            logging.warning(
                "⚠️ Volume ajusté pour %s: demandé=%.6f, normalisé=%.6f (min=%.6f, step=%.6f)",
                symbol,
                desired_volume,
                volume,
                symbol_info.volume_min if symbol_info else 0.0,
                symbol_info.volume_step if symbol_info else 0.0,
            )
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

        start_ts = time.perf_counter()
        result = mt5.order_send(request)
        latency_ms = (time.perf_counter() - start_ts) * 1000.0
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            logging.error("❌ Ordre rejeté: %s", result)
            self.journal.log_event({"type": "order_rejected", "symbol": symbol, "action": action, "result": str(result)})
            return False
        self.risk_manager.record_trade(datetime.now())
        self.last_trade_time = datetime.now()
        self.journal.log_event({
            "type": "order_filled",
            "symbol": symbol,
            "action": action,
            "price": price,
            "latency_ms": round(latency_ms, 1),
        })

        symbol_info = mt5.symbol_info(symbol)
        if symbol_info and hasattr(result, "price"):
            slippage_points = abs(result.price - price) / symbol_info.point
            if slippage_points > DEFAULT_RISK["max_slippage_points"]:
                self.journal.log_event({
                    "type": "slippage_alert",
                    "symbol": symbol,
                    "slippage_points": slippage_points,
                })
                logging.warning("⚠️ Slippage élevé: %.1f points", slippage_points)
        if latency_ms > DEFAULT_RISK["max_latency_ms"]:
            logging.warning("⚠️ Latence élevée: %.0f ms", latency_ms)
        logging.info("✅ Ordre exécuté: %s %s", action, symbol)
        return True

    def should_enter_dormant(self, now: datetime) -> bool:
        if not self.last_trade_time:
            return False
        idle_minutes = (now - self.last_trade_time).total_seconds() / 60.0
        return idle_minutes >= self.dormant_after_minutes

    def dormant_cycle(self):
        if not self.is_dormant:
            self.is_dormant = True
            logging.info("💤 Mode dormant activé (inactivité prolongée)")
        time.sleep(self.dormant_sleep_seconds)

    def run_backtest(self, symbol: str = "BTCUSD", timeframe=mt5.TIMEFRAME_M1, bars: int = 500):
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        if rates is None or len(rates) < 10:
            logging.error("❌ Données insuffisantes pour backtest")
            return

        symbol_info = mt5.symbol_info(symbol)
        point = symbol_info.point if symbol_info else 0.00001
        commission = DEFAULT_RISK["commission_per_lot"]
        slippage_points = DEFAULT_RISK["simulated_slippage_points"]
        volume = SYMBOLS_CONFIG.get(symbol, {}).get("min_lot", 0.01)

        pnl = 0.0
        trades = 0
        wins = 0

        for i in range(1, len(rates)):
            bar = rates[i]
            payload = {
                "context": "entry",
                "symbol": symbol,
                "bid": bar["close"],
                "ask": bar["close"],
                "spread": 0,
                "volume": bar["tick_volume"],
                "timestamp": datetime.fromtimestamp(bar["time"]).isoformat(),
                "risk": MICRO_SCALPING_CONFIG.get("risk_per_trade", 0.5),
            }
            decision = self._request_ai_decision(payload)
            if not decision or decision.get("action") not in ("BUY", "SELL"):
                continue

            next_bar = rates[i + 1] if i + 1 < len(rates) else bar
            spread_points = float(bar["spread"]) if "spread" in bar.dtype.names else 0.0
            spread = spread_points * point
            entry_mid = bar["close"]
            exit_mid = next_bar["close"]

            if decision.get("action") == "BUY":
                entry = entry_mid + (spread / 2) + (slippage_points * point)
                exit_price = exit_mid - (spread / 2) - (slippage_points * point)
                trade_pnl = exit_price - entry
            else:
                entry = entry_mid - (spread / 2) - (slippage_points * point)
                exit_price = exit_mid + (spread / 2) + (slippage_points * point)
                trade_pnl = entry - exit_price

            trade_pnl -= (commission * volume * 2)

            pnl += trade_pnl
            trades += 1
            if trade_pnl > 0:
                wins += 1

        win_rate = (wins / trades * 100) if trades else 0
        logging.info("📊 BACKTEST: trades=%s win_rate=%.1f%% pnl=%.5f", trades, win_rate, pnl)

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

    def run(self):
        last_decision = datetime.now()
        last_health_check = datetime.now()
        last_dormant_check = datetime.now()
        last_ai_heartbeat = datetime.now()

        try:
            while True:
                if not self.verify_connection():
                    time.sleep(2)
                    continue

                now = datetime.now()

                if (now - last_dormant_check).seconds >= self.dormant_check_seconds:
                    if self.should_enter_dormant(now):
                        self.dormant_cycle()
                    else:
                        if self.is_dormant:
                            self.is_dormant = False
                            logging.info("🌞 Réveil automatique")
                    last_dormant_check = now

                if (now - last_decision).seconds >= self.decision_interval_seconds and not self.is_dormant:
                    if self.ai_cooldown_until and now < self.ai_cooldown_until:
                        time.sleep(0.5)
                        continue

                    account_info = mt5.account_info()
                    balance = account_info.balance if account_info else 0.0
                    if self._check_daily_hard_stop(balance):
                        time.sleep(1.0)
                        continue

                    decision = self.executer_strategie_micro_ia()
                    if decision:
                        self.executer_trade(decision)
                    last_decision = now

                if (now - last_health_check).seconds >= 30:
                    if not self.perform_health_check():
                        logging.warning("⚠️ IA indisponible")
                    last_health_check = now

                if (now - last_ai_heartbeat).seconds >= 30:
                    self._check_ai_watchdog()
                    status = "OK" if self.last_ai_error is None else f"ERREUR: {self.last_ai_error}"
                    action = None
                    confidence = None
                    if isinstance(self.last_ai_decision, dict):
                        action = self.last_ai_decision.get("action")
                        confidence = self.last_ai_decision.get("confidence")
                    logging.info(
                        "🧠 IA heartbeat | status=%s | last_action=%s | confidence=%s",
                        status,
                        action,
                        confidence,
                    )
                    last_ai_heartbeat = now

                self._maybe_backup_logs()
                self._maybe_purge_logs()

                time.sleep(0.2 if not self.is_dormant else 1.0)
        except KeyboardInterrupt:
            logging.info("🛑 Arrêt demandé")
        finally:
            self.shutdown()


def parse_arguments():
    parser = argparse.ArgumentParser(description="BTCUSD Micro Scalper V8 PRO - IA")
    parser.add_argument("--real", action="store_true", help="Mode trading réel")
    parser.add_argument("--mode", choices=["MICRO", "AGGRESSIVE", "CONSERVATIVE"], default="MICRO")
    parser.add_argument("--backtest", action="store_true", help="Lancer un backtest IA")
    parser.add_argument("--bars", type=int, default=500, help="Nombre de bougies backtest")
    parser.add_argument("--symbol", type=str, default="BTCUSD", help="Symbole backtest")
    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    args = parse_arguments()

    bot = BTCUSDMicroScalperPro()
    if not bot.initialize(real_trading=args.real, mode=args.mode):
        logging.error("❌ Échec initialisation bot V8 PRO")
        return

    if args.backtest:
        bot.run_backtest(symbol=args.symbol, bars=args.bars)
        return

    bot.run()


if __name__ == "__main__":
    main()
