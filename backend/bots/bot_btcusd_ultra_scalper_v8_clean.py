"""
BTCUSD MICRO SCALPER V8 PRO - Version stable (IA uniquement)
Décision d'entrée/sortie via /api/decision (Groq)
"""

import argparse
import hashlib
import json
import logging
import os
import time
from collections import deque
from datetime import datetime
from typing import Any, Dict, Optional

import MetaTrader5 as mt5
import requests

from backend.config.config_micro_scalping_pro import (
    SYMBOLS_CONFIG,
    MICRO_SCALPING_CONFIG,
    SECURITY_CONFIG,
)


AI_DECISION_URL = os.getenv("AI_ENGINE_URL", "http://127.0.0.1:5003/api/decision")
AI_HEALTH_URL = os.getenv("AI_ENGINE_HEALTH_URL", "http://127.0.0.1:5003/health")

DEFAULT_RISK = {
    "max_trades_per_hour": 12,
    "max_trades_per_day": 120,
    "min_seconds_between_trades": 5,
    "max_daily_loss_pct": 2.0,
    "max_slippage_points": 25,
    "max_latency_ms": 800,
    "commission_per_lot": 0.0,
    "simulated_slippage_points": 5,
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


class BTCUSDMicroScalperPro:
    def __init__(self):
        self.real_trading = False
        self.account = None
        self.active_symbols = [s for s, cfg in SYMBOLS_CONFIG.items() if cfg.get("enabled")]
        self.request_timeout = SECURITY_CONFIG.get("request_timeout", 5)
        self.last_trade_time: Optional[datetime] = None
        self.journal = TradeJournal()
        self.risk_manager: Optional[RiskManager] = None
        self.dormant_after_minutes = 30
        self.dormant_check_seconds = 60
        self.dormant_sleep_seconds = 15
        self.is_dormant = False

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

                if (now - last_decision).seconds >= 3 and not self.is_dormant:
                    decision = self.executer_strategie_micro_ia()
                    if decision:
                        self.executer_trade(decision)
                    last_decision = now

                if (now - last_health_check).seconds >= 30:
                    if not self.perform_health_check():
                        logging.warning("⚠️ IA indisponible")
                    last_health_check = now

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
