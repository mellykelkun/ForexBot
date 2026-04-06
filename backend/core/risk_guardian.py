"""
RISK GUARDIAN — Gestion avancée du risque & protection des fonds
ForexBot SaaS

Fonctionnalités :
  - Global max drawdown (equity, pas seulement journalier)
  - Kill switch d'urgence (ferme tout, bloque le trading)
  - Position sizing dynamique (ATR-based)
  - SL/TP de secours si l'IA n'en fournit pas
  - Vérification des positions ouvertes avant ouverture
  - Vérification latence pré-trade
"""

from __future__ import annotations

import logging
import threading
from collections import deque
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("RiskGuardian")


class RiskGuardian:
    """Risk management avancé — protège le capital en temps réel."""

    def __init__(
        self,
        starting_balance: float,
        initial_capital: float,
        risk_cfg: Optional[Dict[str, Any]] = None,
    ):
        cfg = risk_cfg or {}
        self.starting_balance = starting_balance
        self.initial_capital = initial_capital

        # Limites de trading
        self.max_trades_per_hour: int = int(cfg.get("max_trades_per_hour", 6))
        self.max_trades_per_day: int = int(cfg.get("max_trades_per_day", 60))
        self.min_seconds_between_trades: int = int(cfg.get("min_seconds_between_trades", 15))
        self.max_daily_loss_pct: float = float(cfg.get("max_daily_loss_pct", 2.0))
        self.max_global_drawdown_pct: float = float(cfg.get("max_global_drawdown_pct", 10.0))
        self.max_slippage_points: float = float(cfg.get("max_slippage_points", 25.0))
        self.max_latency_ms: int = int(cfg.get("max_latency_ms", 800))
        self.max_concurrent_positions: int = int(cfg.get("max_concurrent_positions", 3))
        self.risk_per_trade_pct: float = float(cfg.get("risk_per_trade", 0.5))

        # État
        self.trade_times: deque[datetime] = deque(maxlen=2000)
        self.last_trade_time: Optional[datetime] = None
        self.daily_start_balance: float = starting_balance
        self.daily_start_date: str = datetime.now().strftime("%Y-%m-%d")
        self.hard_stop_triggered: bool = False
        self.peak_equity: float = starting_balance
        self._lock = threading.Lock()

        # Kill switch
        self._kill_switch_active: bool = False
        self._kill_switch_reason: str = ""

    # ──────────────────────────────────────────────────────────
    #  Kill Switch
    # ──────────────────────────────────────────────────────────

    def activate_kill_switch(self, reason: str = "Manuel"):
        """Active le kill switch — bloque TOUT trading."""
        with self._lock:
            self._kill_switch_active = True
            self._kill_switch_reason = reason
            logger.critical("🛑 KILL SWITCH ACTIVÉ: %s", reason)

    def deactivate_kill_switch(self):
        """Désactive le kill switch."""
        with self._lock:
            self._kill_switch_active = False
            self._kill_switch_reason = ""
            logger.warning("🟢 Kill switch désactivé")

    @property
    def is_kill_switch_active(self) -> bool:
        return self._kill_switch_active

    @property
    def kill_switch_reason(self) -> str:
        return self._kill_switch_reason

    # ──────────────────────────────────────────────────────────
    #  Core: can_trade() — vérification complète pré-trade
    # ──────────────────────────────────────────────────────────

    def can_trade(
        self,
        now: datetime,
        current_balance: float,
        current_equity: float,
        open_positions_count: int = 0,
        latency_ms: float = 0.0,
    ) -> Tuple[bool, str]:
        """Vérification complète avant d'entrer en position."""
        with self._lock:
            # Kill switch
            if self._kill_switch_active:
                return False, f"KILL SWITCH: {self._kill_switch_reason}"

            # Positions ouvertes max
            if open_positions_count >= self.max_concurrent_positions:
                return False, f"Max positions ouvertes ({self.max_concurrent_positions})"

            # Latence pré-trade
            if latency_ms > self.max_latency_ms:
                return False, f"Latence trop élevée ({latency_ms:.0f}ms > {self.max_latency_ms}ms)"

            # Anti-sur-trading (cooldown)
            if self.last_trade_time:
                dt = (now - self.last_trade_time).total_seconds()
                if dt < self.min_seconds_between_trades:
                    return False, f"Cooldown: {dt:.1f}s < {self.min_seconds_between_trades}s"

            # Prune old trades
            self._prune(now)

            # Trades par heure
            trades_last_hour = sum(
                1 for t in self.trade_times if (now - t).total_seconds() <= 3600
            )
            if trades_last_hour >= self.max_trades_per_hour:
                return False, "Limite trades/heure atteinte"

            # Trades par jour
            if len(self.trade_times) >= self.max_trades_per_day:
                return False, "Limite trades/jour atteinte"

            # Hard stop journalier
            today = now.strftime("%Y-%m-%d")
            if self.daily_start_date != today:
                self.daily_start_date = today
                self.daily_start_balance = current_balance
                self.hard_stop_triggered = False

            if self.hard_stop_triggered:
                return False, "Hard stop journalier déclenché"

            max_daily_loss = -abs(self.daily_start_balance) * (self.max_daily_loss_pct / 100.0)
            daily_pnl = current_balance - self.daily_start_balance
            if daily_pnl <= max_daily_loss:
                self.hard_stop_triggered = True
                logger.warning(
                    "🛑 HARD STOP journalier: PnL %.2f <= %.2f", daily_pnl, max_daily_loss
                )
                return False, "Perte journalière max atteinte"

            # Global drawdown sur equity
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity
            drawdown_pct = 0.0
            if self.peak_equity > 0:
                drawdown_pct = (self.peak_equity - current_equity) / self.peak_equity * 100.0
            if drawdown_pct >= self.max_global_drawdown_pct:
                self._kill_switch_active = True
                self._kill_switch_reason = (
                    f"Global drawdown {drawdown_pct:.1f}% >= {self.max_global_drawdown_pct}%"
                )
                logger.critical("🛑 GLOBAL DRAWDOWN KILL: %.1f%%", drawdown_pct)
                return False, self._kill_switch_reason

            return True, "OK"

    def record_trade(self, when: datetime):
        """Enregistre un trade effectué."""
        with self._lock:
            self.trade_times.append(when)
            self.last_trade_time = when

    def _prune(self, now: datetime):
        """Supprime les trades de plus de 24h."""
        while self.trade_times and (now - self.trade_times[0]).total_seconds() > 86400:
            self.trade_times.popleft()

    # ──────────────────────────────────────────────────────────
    #  Position Sizing dynamique
    # ──────────────────────────────────────────────────────────

    def calculate_position_size(
        self,
        balance: float,
        atr_value: float,
        symbol_point: float,
        tick_value: float,
        volume_min: float,
        volume_max: float,
        volume_step: float,
        risk_multiplier: float = 1.0,
    ) -> float:
        """
        Position sizing basé sur le risque et l'ATR.
        Volume = (balance * risk% * multiplier) / (ATR_ticks * tick_value)

        tick_value = symbol_info.trade_tick_value (valeur monétaire d'1 tick pour 1 lot)
        """
        if atr_value <= 0 or symbol_point <= 0 or tick_value <= 0:
            logger.warning("⚠️ Position sizing: paramètre invalide (atr=%.6f, point=%.6f, tick_val=%.4f) → volume_min",
                           atr_value, symbol_point, tick_value)
            return volume_min

        risk_amount = balance * (self.risk_per_trade_pct / 100.0) * risk_multiplier
        # ATR en nombre de ticks (points)
        atr_ticks = atr_value / symbol_point
        if atr_ticks <= 0:
            return volume_min

        # Volume = risque monétaire / (nombre de ticks de SL × valeur d'1 tick par lot)
        desired = risk_amount / (atr_ticks * tick_value)

        logger.info("📐 Position sizing: balance=%.2f, risk_amount=%.2f, atr=%.6f, "
                     "atr_ticks=%.1f, tick_value=%.4f, raw_volume=%.6f",
                     balance, risk_amount, atr_value, atr_ticks, tick_value, desired)

        desired = max(desired, volume_min)
        desired = min(desired, volume_max)

        # Arrondi au step
        if volume_step > 0:
            steps = int(desired / volume_step)
            desired = steps * volume_step

        desired = max(desired, volume_min)
        desired = min(desired, volume_max)
        return round(desired, 6)

    # ──────────────────────────────────────────────────────────
    #  Validation des stops vs stop level broker
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def validate_stops_distance(
        action: str,
        entry_price: float,
        sl: float,
        tp: float,
        stops_level: int,
        symbol_point: float,
        spread_points: float = 0.0,
    ) -> Tuple[float, float]:
        """
        Vérifie que SL et TP respectent la distance minimale du broker
        (trade_stops_level). Si non, élargit au minimum autorisé.
        spread_points = spread actuel en points (pour ajouter une marge).
        """
        # Distance minimale en prix = (stops_level + marge spread) × point
        min_distance = (stops_level + spread_points + 5) * symbol_point  # +5 pts de sécurité

        if min_distance <= 0:
            return sl, tp

        sl_dist = abs(sl - entry_price)
        tp_dist = abs(tp - entry_price)

        if sl_dist < min_distance:
            old_sl = sl
            if action == "BUY":
                sl = entry_price - min_distance
            else:
                sl = entry_price + min_distance
            logger.warning("⚠️ SL trop proche (%.5f, dist=%.5f < min=%.5f) → ajusté: %.5f",
                           old_sl, sl_dist, min_distance, sl)

        if tp_dist < min_distance:
            old_tp = tp
            if action == "BUY":
                tp = entry_price + min_distance
            else:
                tp = entry_price - min_distance
            logger.warning("⚠️ TP trop proche (%.5f, dist=%.5f < min=%.5f) → ajusté: %.5f",
                           old_tp, tp_dist, min_distance, tp)

        return round(sl, 6), round(tp, 6)

    # ──────────────────────────────────────────────────────────
    #  SL/TP de secours (ATR-based)
    # ──────────────────────────────────────────────────────────

    def fallback_sl_tp(
        self,
        action: str,
        entry_price: float,
        atr_value: Optional[float],
        symbol_point: float,
        sl_from_ia: Optional[float] = None,
        tp_from_ia: Optional[float] = None,
        sl_atr_mult: float = 1.5,
        tp_atr_mult: float = 2.0,
    ) -> Tuple[float, float]:
        """
        Retourne (sl, tp). Utilise les valeurs IA si fournies et valides,
        sinon calcule un SL/TP de secours basé sur l'ATR.
        """
        # ATR fallback par défaut
        if atr_value is None or atr_value <= 0:
            atr_value = entry_price * 0.002  # 0.2% fallback

        atr_sl = atr_value * sl_atr_mult
        atr_tp = atr_value * tp_atr_mult

        if action == "BUY":
            default_sl = entry_price - atr_sl
            default_tp = entry_price + atr_tp
        else:  # SELL
            default_sl = entry_price + atr_sl
            default_tp = entry_price - atr_tp

        # Valider SL de l'IA
        sl = sl_from_ia
        if sl is None or sl <= 0:
            sl = default_sl
            logger.warning("⚠️ SL IA absent → fallback ATR: %.5f", sl)
        elif action == "BUY" and sl >= entry_price:
            sl = default_sl
            logger.warning("⚠️ SL BUY invalide (>= entry) → fallback ATR: %.5f", sl)
        elif action == "SELL" and sl <= entry_price:
            sl = default_sl
            logger.warning("⚠️ SL SELL invalide (<= entry) → fallback ATR: %.5f", sl)

        # Valider TP de l'IA
        tp = tp_from_ia
        if tp is None or tp <= 0:
            tp = default_tp
            logger.warning("⚠️ TP IA absent → fallback ATR: %.5f", tp)
        elif action == "BUY" and tp <= entry_price:
            tp = default_tp
            logger.warning("⚠️ TP BUY invalide (<= entry) → fallback ATR: %.5f", tp)
        elif action == "SELL" and tp >= entry_price:
            tp = default_tp
            logger.warning("⚠️ TP SELL invalide (>= entry) → fallback ATR: %.5f", tp)

        return round(sl, 6), round(tp, 6)

    # ──────────────────────────────────────────────────────────
    #  Stats pour payload IA
    # ──────────────────────────────────────────────────────────

    def get_risk_state(self, now: datetime, balance: float, equity: float) -> Dict[str, Any]:
        """Retourne l'état du risk management pour le payload IA."""
        with self._lock:
            self._prune(now)
            trades_last_hour = sum(
                1 for t in self.trade_times if (now - t).total_seconds() <= 3600
            )
            daily_pnl = balance - self.daily_start_balance
            drawdown_pct = 0.0
            if self.peak_equity > 0:
                drawdown_pct = (self.peak_equity - equity) / self.peak_equity * 100.0

            return {
                "balance": round(balance, 2),
                "equity": round(equity, 2),
                "daily_pnl": round(daily_pnl, 2),
                "daily_pnl_pct": round(daily_pnl / max(self.daily_start_balance, 1) * 100, 2),
                "global_drawdown_pct": round(drawdown_pct, 2),
                "peak_equity": round(self.peak_equity, 2),
                "trades_last_hour": trades_last_hour,
                "trades_today": len(self.trade_times),
                "last_trade_seconds_ago": (
                    round((now - self.last_trade_time).total_seconds(), 1)
                    if self.last_trade_time
                    else None
                ),
                "kill_switch": self._kill_switch_active,
                "hard_stop": self.hard_stop_triggered,
            }
