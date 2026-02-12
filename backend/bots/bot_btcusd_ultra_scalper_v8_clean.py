"""
BTCUSD MICRO SCALPER V8 PRO - Version stable (IA uniquement)
Décision d'entrée/sortie via /api/decision (Multi-Provider: Groq/OpenAI/DeepSeek)
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

from backend.utils import get_logger
from backend.config.config_micro_scalping_pro import (
    SYMBOLS_CONFIG,
    MICRO_SCALPING_CONFIG,
    SECURITY_CONFIG,
)
from backend.core import indicators as ind
from backend.core.risk_guardian import RiskGuardian
from backend.core.smart_payload import build_smart_payload, estimate_token_count

import numpy as _np

def _sanitize_for_json(obj):
    """Convertit récursivement les types numpy en types Python natifs pour JSON."""
    if isinstance(obj, dict):
        return {k: _sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_for_json(v) for v in obj]
    if isinstance(obj, (_np.bool_,)):
        return bool(obj)
    if isinstance(obj, (_np.integer,)):
        return int(obj)
    if isinstance(obj, (_np.floating,)):
        return float(obj)
    if isinstance(obj, _np.ndarray):
        return obj.tolist()
    return obj
from backend.core.position_monitor import PositionMonitor


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


# RiskManager remplacé par RiskGuardian (backend.core.risk_guardian)
# Gestion avancée: global drawdown, kill switch, position sizing ATR, fallback SL/TP


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
        self.risk_guardian: Optional[RiskGuardian] = None
        self.position_monitor: Optional[PositionMonitor] = None
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
        self.bars_m1 = _env_int("BARS_M1", 1000)
        self.bars_m5 = _env_int("BARS_M5", 1000)
        self.bars_h1 = _env_int("BARS_H1", 2000)
        self.bars_h4 = _env_int("BARS_H4", 2000)
        self.bars_d1 = _env_int("BARS_D1", 2000)
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
        self.risk_guardian = RiskGuardian(
            starting_balance=self.account.balance,
            initial_capital=self.account.balance,
            risk_cfg={
                "max_trades_per_hour": DEFAULT_RISK["max_trades_per_hour"],
                "max_trades_per_day": DEFAULT_RISK["max_trades_per_day"],
                "min_seconds_between_trades": DEFAULT_RISK["min_seconds_between_trades"],
                "max_daily_loss_pct": DEFAULT_RISK["max_daily_loss_pct"],
                "max_slippage_points": DEFAULT_RISK["max_slippage_points"],
                "max_latency_ms": DEFAULT_RISK["max_latency_ms"],
                "max_concurrent_positions": 3,
                "risk_per_trade": MICRO_SCALPING_CONFIG.get("risk_per_trade", 0.5),
            },
        )
        # Position Monitor — surveillance continue des positions ouvertes
        self.position_monitor = PositionMonitor(
            mt5_api=mt5,
            get_decision_func=self._request_ai_decision,
            check_interval=30.0,
        )
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

    # ── Indicateurs déplacés → backend.core.indicators (corrigés Wilder/chrono) ──

    def _get_market_data(self, symbol: str, timeframe, bars: int = 200) -> Optional[Dict[str, list]]:
        """Récupère les données de marché depuis MT5 et retourne les séries OHLCV."""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        if rates is None or len(rates) < 30:
            return None
        # Index 0 = plus récent (convention du bot)
        closes = [r["close"] for r in rates][::-1]
        highs = [r["high"] for r in rates][::-1]
        lows = [r["low"] for r in rates][::-1]
        opens = [r["open"] for r in rates][::-1]
        volumes = [r["tick_volume"] for r in rates][::-1]
        return {
            "close": closes, "high": highs, "low": lows,
            "open": opens, "volume": volumes,
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

    def _get_recent_trade_history(self, symbol: str, max_trades: int = 10) -> list:
        """
        Récupère les N derniers trades fermés depuis MT5 pour ce symbole.
        Retourne une liste de résumés (profit, raison de clôture, etc.)
        pour que l'IA puisse analyser ses propres performances.
        """
        try:
            from datetime import timedelta
            now = datetime.now()
            # Chercher les deals des dernières 48h
            deals = mt5.history_deals_get(now - timedelta(hours=48), now, group=f"*{symbol}*")
            if not deals:
                return []

            # Filtrer uniquement les clôtures (DEAL_ENTRY_OUT=1) et prendre les plus récents
            closed_trades = []
            for deal in deals:
                if deal.entry != 1:  # 1 = DEAL_ENTRY_OUT (fermeture)
                    continue
                # Déterminer la raison de clôture
                reason_map = {
                    0: "manual",       # CLIENT
                    3: "stop_loss",    # SL
                    4: "take_profit",  # TP
                    5: "stop_out",     # STOP OUT (margin call)
                    6: "rollover",
                    7: "vmargin",
                }
                close_reason = reason_map.get(deal.reason, f"other({deal.reason})")

                closed_trades.append({
                    "ticket": deal.ticket,
                    "type": "BUY" if deal.type == 0 else "SELL",
                    "volume": deal.volume,
                    "price": round(deal.price, 6),
                    "profit": round(deal.profit, 2),
                    "commission": round(deal.commission, 2) if deal.commission else 0.0,
                    "swap": round(deal.swap, 2) if deal.swap else 0.0,
                    "close_reason": close_reason,
                    "time": datetime.fromtimestamp(deal.time).strftime("%Y-%m-%d %H:%M"),
                })

            # Prendre les N derniers
            closed_trades = closed_trades[-max_trades:]

            return closed_trades
        except Exception as e:
            logging.warning("⚠️ Impossible de récupérer l'historique trades: %s", e)
            return []

    def _build_trade_performance_summary(self, symbol: str) -> dict:
        """
        Construit un résumé de performance que l'IA peut utiliser pour
        s'auto-évaluer et apprendre de ses erreurs.
        """
        history = self._get_recent_trade_history(symbol, max_trades=15)
        if not history:
            return {"recent_trades": [], "stats": {"total": 0}}

        total = len(history)
        wins = [t for t in history if t["profit"] > 0]
        losses = [t for t in history if t["profit"] < 0]
        sl_hits = [t for t in history if t["close_reason"] == "stop_loss"]
        tp_hits = [t for t in history if t["close_reason"] == "take_profit"]

        total_profit = sum(t["profit"] for t in wins)
        total_loss = sum(t["profit"] for t in losses)
        net_pnl = total_profit + total_loss

        # Séquence actuelle (streak)
        streak = 0
        streak_type = None
        for t in reversed(history):
            if streak_type is None:
                streak_type = "win" if t["profit"] > 0 else "loss"
                streak = 1
            elif (streak_type == "win" and t["profit"] > 0) or (streak_type == "loss" and t["profit"] <= 0):
                streak += 1
            else:
                break

        stats = {
            "total": total,
            "wins": len(wins),
            "losses": len(losses),
            "win_rate_pct": round(len(wins) / total * 100, 1) if total > 0 else 0,
            "net_pnl": round(net_pnl, 2),
            "total_profit": round(total_profit, 2),
            "total_loss": round(total_loss, 2),
            "avg_win": round(total_profit / len(wins), 2) if wins else 0,
            "avg_loss": round(total_loss / len(losses), 2) if losses else 0,
            "sl_hit_count": len(sl_hits),
            "tp_hit_count": len(tp_hits),
            "current_streak": f"{streak} consecutive {'wins' if streak_type == 'win' else 'losses'}" if streak_type else "none",
        }

        # Garder seulement les 5 derniers trades pour le payload (économie de tokens)
        recent = history[-5:]

        return {
            "recent_trades": recent,
            "stats": stats,
        }

    def _build_payload(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Construit le payload sémantique compressé pour l'IA."""
        tick = self._get_symbol_tick(symbol)
        if not tick:
            return None
        symbol_info = mt5.symbol_info(symbol)
        spread_points = None
        if symbol_info and symbol_info.point:
            spread_points = tick["spread"] / symbol_info.point

        # Récupérer données multi-timeframe (barres réduites vs avant)
        tf_map = {
            "M1":  (mt5.TIMEFRAME_M1,  min(self.bars_m1, 200)),
            "M5":  (mt5.TIMEFRAME_M5,  min(self.bars_m5, 200)),
            "H1":  (mt5.TIMEFRAME_H1,  min(self.bars_h1, 500)),
            "H4":  (mt5.TIMEFRAME_H4,  min(self.bars_h4, 300)),
            "D1":  (mt5.TIMEFRAME_D1,  min(self.bars_d1, 200)),
        }
        timeframes_data = {}
        atr_m1 = None
        for tf_name, (tf_const, bars_count) in tf_map.items():
            data = self._get_market_data(symbol, tf_const, bars_count)
            if data:
                timeframes_data[tf_name] = data
                # Récupérer ATR M1 pour le position sizing et fallback SL/TP
                if tf_name == "M1":
                    atr_m1 = ind.atr(data["high"], data["low"], data["close"], 14)
                    # Mettre à jour l'ATR dans le position monitor
                    if self.position_monitor:
                        self.position_monitor.update_atr(symbol, atr_m1 or 0)

        # État du risk guardian
        account_info = mt5.account_info()
        balance = account_info.balance if account_info else 0.0
        equity = account_info.equity if account_info else 0.0
        risk_state = self.risk_guardian.get_risk_state(datetime.now(), balance, equity)

        # Positions ouvertes
        open_positions = []
        try:
            positions = mt5.positions_get(symbol=symbol)
            if positions:
                for pos in positions:
                    open_positions.append({
                        "ticket": pos.ticket,
                        "type": "BUY" if pos.type == 0 else "SELL",
                        "volume": pos.volume,
                        "price_open": pos.price_open,
                        "sl": pos.sl,
                        "tp": pos.tp,
                        "profit": pos.profit,
                        "time_open": pos.time,
                    })
        except Exception:
            pass

        # Construire le payload sémantique compressé
        payload = build_smart_payload(
            symbol=symbol,
            timeframes_data=timeframes_data,
            risk_state=risk_state,
            open_positions=open_positions,
            context="entry",
            extra={
                "bid": tick["bid"],
                "ask": tick["ask"],
                "spread_points": spread_points,
                "constraints": {
                    "min_seconds_between_trades": DEFAULT_RISK["min_seconds_between_trades"],
                    "max_trades_per_hour": DEFAULT_RISK["max_trades_per_hour"],
                    "max_trades_per_day": DEFAULT_RISK["max_trades_per_day"],
                    "required_confidence": self.required_confidence,
                },
            },
        )

        # ── Historique des performances IA (auto-évaluation) ──
        try:
            perf = self._build_trade_performance_summary(symbol)
            if perf.get("stats", {}).get("total", 0) > 0:
                payload["my_trade_history"] = perf
        except Exception as e:
            logging.warning("⚠️ Historique performance non disponible: %s", e)

        # Stocker l'ATR pour le fallback SL/TP
        payload["_atr_m1"] = atr_m1
        payload["_symbol_point"] = symbol_info.point if symbol_info else 0.00001

        return payload

    def _request_ai_decision(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            payload = _sanitize_for_json(payload)
            # Retirer les champs internes (préfixés _) avant envoi à l'IA
            ai_payload = {k: v for k, v in payload.items() if not k.startswith("_")}
            try:
                payload_size = len(json.dumps(ai_payload, ensure_ascii=False))
                try:
                    get_logger().info(f"📦 Payload IA {ai_payload.get('symbol')}: {payload_size} bytes")
                except Exception:
                    logging.info("📦 Payload IA %s: %s bytes", ai_payload.get("symbol"), payload_size)
            except Exception:
                pass
            resp = requests.post(
                AI_DECISION_URL,
                json=ai_payload,
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
                    json=ai_payload,
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

        # Rotation des backups : supprimer les dossiers > 7 jours
        self._cleanup_old_backups(max_age_days=7)

        self.backup_last_run = now

    def _cleanup_old_backups(self, max_age_days: int = 7):
        """Supprime les dossiers de backup plus vieux que max_age_days."""
        backup_base = "backups"
        if not os.path.isdir(backup_base):
            return
        cutoff = datetime.now() - timedelta(days=max_age_days)
        for name in sorted(os.listdir(backup_base)):
            folder = os.path.join(backup_base, name)
            if not os.path.isdir(folder):
                continue
            try:
                folder_date = datetime.strptime(name, "%Y%m%d")
                if folder_date < cutoff:
                    shutil.rmtree(folder, ignore_errors=True)
                    logging.info("🗑️ Backup ancien supprimé: %s", folder)
            except ValueError:
                continue

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

        def _size_mb(path: str) -> float:
            try:
                return os.path.getsize(path) / (1024 * 1024)
            except Exception:
                return 0.0

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
                else:
                    logging.info("ℹ️ Pas de purge (taille trop petite): %s (%.2f MB)", path, _size_mb(path))

        if _should_purge("process_manager.log"):
            _truncate("process_manager.log")
        else:
            if os.path.exists("process_manager.log"):
                logging.info("ℹ️ Pas de purge (taille trop petite): %s (%.2f MB)", "process_manager.log", _size_mb("process_manager.log"))

        self.log_purge_last_run = now

    def executer_strategie_micro_ia(self) -> Optional[Dict[str, Any]]:
        for symbol in self.active_symbols:
            payload = self._build_payload(symbol)
            if not payload:
                continue
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info and symbol_info.point:
                spread_points = payload.get("extra", {}).get("spread_points")
                if spread_points is not None:
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

            # Log taille payload compressé
            try:
                tokens_est = estimate_token_count(payload)
                logging.info("📦 Payload IA %s: ~%d tokens (compression sémantique)", symbol, tokens_est)
            except Exception:
                pass

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
                decision["_payload"] = payload  # Conserver payload pour position sizing
                return decision
        return None

    def executer_trade(self, decision: Dict[str, Any], payload: Optional[Dict[str, Any]] = None) -> bool:
        symbol = decision.get("symbol")
        action = decision.get("action")
        if not symbol or action not in ("BUY", "SELL"):
            return False

        if not self.risk_guardian:
            return False

        account_info = mt5.account_info()
        balance = account_info.balance if account_info else 0.0
        equity = account_info.equity if account_info else balance

        # Compter les positions ouvertes
        open_positions = mt5.positions_get()
        open_count = len(open_positions) if open_positions else 0

        # Mesurer latence pré-trade (ping MT5)
        latency_start = time.perf_counter()
        _ = mt5.symbol_info_tick(symbol)
        latency_ms = (time.perf_counter() - latency_start) * 1000.0

        ok, reason = self.risk_guardian.can_trade(
            now=datetime.now(),
            current_balance=balance,
            current_equity=equity,
            open_positions_count=open_count,
            latency_ms=latency_ms,
        )
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

        # Position sizing dynamique basé sur ATR
        atr_value = (payload or {}).get("_atr_m1") or 0
        sym_point = (payload or {}).get("_symbol_point") or (symbol_info.point if symbol_info else 0.00001)

        # Récupérer tick_value, risk_multiplier et max_lot depuis MT5 + SYMBOLS_CONFIG
        tick_value = symbol_info.trade_tick_value if symbol_info and symbol_info.trade_tick_value else 1.0
        sym_cfg = SYMBOLS_CONFIG.get(symbol, {})
        risk_mult = sym_cfg.get("risk_multiplier", 1.0)
        config_max_lot = sym_cfg.get("max_lot", 0.03)
        config_min_lot = sym_cfg.get("min_lot", 0.001)

        # Plafond de volume = min(broker max, config max)
        effective_max = min(
            symbol_info.volume_max if symbol_info and symbol_info.volume_max else 100.0,
            config_max_lot,
        )

        desired_volume = self.risk_guardian.calculate_position_size(
            balance=balance,
            atr_value=atr_value if atr_value > 0 else sym_point * 100,
            symbol_point=sym_point,
            tick_value=tick_value,
            volume_min=max(symbol_info.volume_min if symbol_info else 0.01, config_min_lot),
            volume_max=effective_max,
            volume_step=symbol_info.volume_step if symbol_info else 0.01,
            risk_multiplier=risk_mult,
        )
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

        price = tick.ask if action == "BUY" else tick.bid

        # SL/TP de secours si l'IA n'en fournit pas ou renvoie des valeurs invalides
        sl_ia = decision.get("sl_price")
        tp_ia = decision.get("tp_price")
        sl, tp = self.risk_guardian.fallback_sl_tp(
            action=action,
            entry_price=price,
            atr_value=atr_value if atr_value > 0 else None,
            symbol_point=sym_point,
            sl_from_ia=sl_ia,
            tp_from_ia=tp_ia,
        )

        # ── Validation des stops vs stop level broker ──
        stops_level = symbol_info.trade_stops_level if symbol_info else 0
        spread_pts = (tick.ask - tick.bid) / sym_point if sym_point > 0 else 0
        sl, tp = self.risk_guardian.validate_stops_distance(
            action=action,
            entry_price=price,
            sl=sl,
            tp=tp,
            stops_level=int(stops_level),
            symbol_point=sym_point,
            spread_points=spread_pts,
        )

        if abs(volume - desired_volume) > 1e-9:
            logging.warning(
                "⚠️ Volume ajusté pour %s: demandé=%.6f, normalisé=%.6f (min=%.6f, step=%.6f)",
                symbol,
                desired_volume,
                volume,
                symbol_info.volume_min if symbol_info else 0.0,
                symbol_info.volume_step if symbol_info else 0.0,
            )

        logging.info("📤 Ordre %s %s: vol=%.4f, prix=%.5f, SL=%.5f, TP=%.5f, stops_level=%d",
                      action, symbol, volume, price, sl, tp, int(stops_level))

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
        exec_latency_ms = (time.perf_counter() - start_ts) * 1000.0
        if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
            logging.error("❌ Ordre rejeté: %s", result)
            self.journal.log_event({"type": "order_rejected", "symbol": symbol, "action": action, "result": str(result)})
            return False
        self.risk_guardian.record_trade(datetime.now())
        self.last_trade_time = datetime.now()
        self.journal.log_event({
            "type": "order_filled",
            "symbol": symbol,
            "action": action,
            "price": price,
            "latency_ms": round(exec_latency_ms, 1),
            "volume": volume,
            "sl": sl,
            "tp": tp,
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
            logging.warning("⚠️ Latence exécution élevée: %.0f ms", exec_latency_ms)
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
            if self.position_monitor:
                self.position_monitor.stop()
        except Exception:
            pass
        try:
            mt5.shutdown()
        except Exception:
            pass

    def run(self):
        last_decision = datetime.now()
        last_health_check = datetime.now()
        last_dormant_check = datetime.now()
        last_ai_heartbeat = datetime.now()

        # Démarrer le Position Monitor (surveillance continue des positions + trailing stop)
        if self.position_monitor and self.real_trading:
            self.position_monitor.start()

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
                        self.executer_trade(decision, payload=decision.pop("_payload", None))
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
