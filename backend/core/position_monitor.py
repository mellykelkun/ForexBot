"""
POSITION MONITOR — Surveillance des positions ouvertes & gestion de sortie
ForexBot SaaS

Fonctionnalités :
  - Suivi continu des positions ouvertes via MT5
  - Envoi de requêtes exit à l'IA avec contexte de la position
  - Trailing stop dynamique
  - Breakeven automatique
  - Fermeture d'urgence
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("PositionMonitor")


class PositionMonitor:
    """Surveille les positions ouvertes et gère les sorties."""

    def __init__(
        self,
        mt5_api,
        get_decision_func: Callable,
        check_interval: float = 30.0,
        trailing_stop_atr_mult: float = 1.0,
        breakeven_trigger_atr: float = 1.5,
    ):
        """
        Args:
            mt5_api: Objet MetaTrader5 ou wrapper avec positions_get(), etc.
            get_decision_func: Fonction qui prend un payload et retourne la décision IA.
            check_interval: Intervalle en secondes entre chaque vérification.
            trailing_stop_atr_mult: Multiplicateur ATR pour le trailing stop.
            breakeven_trigger_atr: Distance en ATR avant activation du breakeven.
        """
        self.mt5 = mt5_api
        self.get_decision = get_decision_func
        self.check_interval = check_interval
        self.trailing_stop_atr_mult = trailing_stop_atr_mult
        self.breakeven_trigger_atr = breakeven_trigger_atr
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._symbol_atrs: Dict[str, float] = {}

    def start(self):
        """Démarre le monitoring en background."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="PositionMonitor")
        self._thread.start()
        logger.info("📊 Position Monitor démarré (interval: %.1fs)", self.check_interval)

    def stop(self):
        """Arrête le monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("📊 Position Monitor arrêté")

    def update_atr(self, symbol: str, atr_value: float):
        """Met à jour l'ATR d'un symbole (appelé par le bot quand il calcule)."""
        with self._lock:
            self._symbol_atrs[symbol] = atr_value

    def _monitor_loop(self):
        """Boucle principale du monitor."""
        while self._running:
            try:
                self._check_positions()
            except Exception as e:
                logger.error("❌ Erreur PositionMonitor: %s", e)
            time.sleep(self.check_interval)

    def _check_positions(self):
        """Vérifie toutes les positions ouvertes."""
        try:
            positions = self.mt5.positions_get()
        except Exception as e:
            logger.error("Impossible de récupérer les positions: %s", e)
            return

        if not positions:
            return

        for pos in positions:
            try:
                self._evaluate_position(pos)
            except Exception as e:
                ticket = getattr(pos, "ticket", "?")
                logger.error("Erreur évaluation position %s: %s", ticket, e)

    def _evaluate_position(self, position):
        """Évalue une position individuelle."""
        ticket = position.ticket
        symbol = position.symbol
        pos_type = "BUY" if position.type == 0 else "SELL"
        volume = position.volume
        price_open = position.price_open
        current_price = position.price_current
        sl = position.sl
        tp = position.tp
        profit = position.profit
        time_open = position.time

        # Temps ouvert en secondes
        now = datetime.now()
        open_seconds = (now - datetime.fromtimestamp(time_open)).total_seconds()

        # ATR du symbole
        with self._lock:
            atr = self._symbol_atrs.get(symbol, 0)

        # Calcul du P&L en pips approximatifs
        point = getattr(position, "point", None)
        if not point:
            try:
                info = self.mt5.symbol_info(symbol)
                point = info.point if info else 0.00001
            except Exception:
                point = 0.00001

        if pos_type == "BUY":
            pnl_points = (current_price - price_open) / point
        else:
            pnl_points = (price_open - current_price) / point

        # Breakeven automatique
        if atr > 0 and sl > 0:
            self._check_breakeven(position, pos_type, price_open, current_price, sl, atr, point)

        # Trailing stop
        if atr > 0 and sl > 0:
            self._check_trailing_stop(position, pos_type, current_price, sl, atr)

        # Log
        logger.debug(
            "📊 Position %s %s %s: P&L=%.2f pts, Profit=%.2f, Ouvert depuis %.0fs",
            ticket, pos_type, symbol, pnl_points, profit, open_seconds,
        )

    def _check_breakeven(
        self, position, pos_type: str, entry: float,
        current: float, sl: float, atr: float, point: float,
    ):
        """Active le breakeven si le prix a bougé de breakeven_trigger_atr * ATR."""
        trigger = atr * self.breakeven_trigger_atr

        if pos_type == "BUY":
            if current - entry >= trigger and sl < entry:
                new_sl = entry + point * 5  # 5 points au-dessus de l'entrée
                self._modify_sl(position, new_sl)
                logger.info(
                    "🔒 Breakeven activé ticket %s: SL → %.5f", position.ticket, new_sl
                )
        else:  # SELL
            if entry - current >= trigger and sl > entry:
                new_sl = entry - point * 5
                self._modify_sl(position, new_sl)
                logger.info(
                    "🔒 Breakeven activé ticket %s: SL → %.5f", position.ticket, new_sl
                )

    def _check_trailing_stop(
        self, position, pos_type: str, current: float, sl: float, atr: float,
    ):
        """Trailing stop basé sur l'ATR."""
        trail_dist = atr * self.trailing_stop_atr_mult

        if pos_type == "BUY":
            ideal_sl = current - trail_dist
            if ideal_sl > sl:
                self._modify_sl(position, ideal_sl)
                logger.info(
                    "📈 Trailing stop ticket %s: SL → %.5f (diff +%.5f)",
                    position.ticket, ideal_sl, ideal_sl - sl,
                )
        else:  # SELL
            ideal_sl = current + trail_dist
            if ideal_sl < sl:
                self._modify_sl(position, ideal_sl)
                logger.info(
                    "📉 Trailing stop ticket %s: SL → %.5f (diff -%.5f)",
                    position.ticket, ideal_sl, sl - ideal_sl,
                )

    def _modify_sl(self, position, new_sl: float):
        """Modifie le SL d'une position via MT5."""
        try:
            import MetaTrader5 as mt5

            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": position.ticket,
                "symbol": position.symbol,
                "sl": round(new_sl, position.digits if hasattr(position, "digits") else 5),
                "tp": position.tp,
            }
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info("✅ SL modifié ticket %s → %.5f", position.ticket, new_sl)
            else:
                retcode = result.retcode if result else "None"
                logger.warning("⚠️ Échec modification SL ticket %s: %s", position.ticket, retcode)
        except Exception as e:
            logger.error("❌ Erreur modification SL: %s", e)

    def emergency_close_all(self, reason: str = "Kill switch"):
        """Ferme d'urgence TOUTES les positions ouvertes."""
        logger.critical("🛑 FERMETURE D'URGENCE: %s", reason)
        try:
            import MetaTrader5 as mt5

            positions = mt5.positions_get()
            if not positions:
                logger.info("Aucune position à fermer")
                return 0

            closed = 0
            for pos in positions:
                try:
                    pos_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
                    price = mt5.symbol_info_tick(pos.symbol)
                    close_price = price.bid if pos.type == 0 else price.ask

                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": pos.symbol,
                        "volume": pos.volume,
                        "type": pos_type,
                        "position": pos.ticket,
                        "price": close_price,
                        "deviation": 50,
                        "magic": 999999,
                        "comment": f"Emergency: {reason}",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    result = mt5.order_send(request)
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        closed += 1
                        logger.info("✅ Position %s fermée d'urgence", pos.ticket)
                    else:
                        retcode = result.retcode if result else "None"
                        logger.error("❌ Échec fermeture position %s: %s", pos.ticket, retcode)
                except Exception as e:
                    logger.error("❌ Erreur fermeture position %s: %s", pos.ticket, e)

            logger.critical("🛑 Fermeture d'urgence: %d/%d positions fermées", closed, len(positions))
            return closed

        except Exception as e:
            logger.critical("❌ ERREUR CRITIQUE fermeture d'urgence: %s", e)
            return 0
