"""
MOTEUR IA - Groq uniquement (IA autonome)
Tout traitement local/heuristique supprimé.
Sécurisé: écoute 127.0.0.1 uniquement + token API.
"""

from datetime import datetime

import logging
from flask import Flask, jsonify, request

from backend.ai.groq_service import GroqService
from backend.security.auth import require_api_token


class AdaptiveAIEngine:
    def __init__(self):
        self.groq = GroqService()

    # ── System prompt (English for better LLM performance) ─────────────
    SYSTEM_PROMPT = (
        "You are an autonomous trading decision engine. "
        "Return ONLY a strict JSON object — no prose, no markdown.\n\n"

        # ── Payload structure the model receives ──
        "== PAYLOAD STRUCTURE ==\n"
        "symbol: trading pair (e.g. BTCUSD, EURUSD).\n"
        "context: 'entry' (should I open?) or 'exit' (should I close?).\n"
        "multi_timeframe: dict of timeframe summaries (M1, M5, H1, H4, D1). "
        "Each contains: price, trend {direction, strength, ema_alignment}, "
        "volatility {regime, atr_pct, bb_width_pct, squeeze}, "
        "momentum {rsi, rsi_zone, macd_histogram, macd_direction, stochastic_k/d, mfi}, "
        "confluence {bias, score, bull_signals, bear_signals}, "
        "key_levels {pivot, fibonacci}, market_regime, candle_patterns.\n"
        "mtf_synthesis: overall multi-timeframe summary with overall_bias, alignment, "
        "bullish_count, bearish_count. Use this as the PRIMARY directional signal.\n"
        "risk_state: current risk status (can_trade, drawdown, daily_pnl, kill_switch).\n"
        "open_positions: list of current open trades with ticket, type, volume, profit.\n"
        "extra: contains bid, ask, spread_points, and constraints.\n\n"

        # ── Decision rules ──
        "== DECISION RULES ==\n"
        "1. DEFAULT is HOLD. Only output BUY or SELL when ALL of these are true:\n"
        "   a) mtf_synthesis.alignment = ALIGNED (most timeframes agree).\n"
        "   b) At least 2 timeframes show confluence.score >= 60.\n"
        "   c) M1 or M5 momentum aligns with the higher-timeframe trend.\n"
        "   d) market_regime is TRENDING_UP or TRENDING_DOWN (not RANGING).\n"
        "   e) No conflicting candle_patterns (e.g. reversal pattern against trend).\n"
        "2. If context='exit': action ∈ {EXIT, HOLD}. EXIT when reversal signals appear "
        "or profit target zone reached.\n\n"

        # ── Constraints (hard rules — never override) ──
        "== HARD CONSTRAINTS ==\n"
        "If extra.constraints exists, enforce these BEFORE any analysis:\n"
        "- trade_state.last_trade_seconds_ago < constraints.min_seconds_between_trades → HOLD.\n"
        "- trade_state.trades_last_hour >= constraints.max_trades_per_hour → HOLD.\n"
        "- trade_state.trades_last_day >= constraints.max_trades_per_day → HOLD.\n"
        "- risk_state.can_trade = false → HOLD.\n"
        "- extra.spread_points > 50 → HOLD (spread too wide).\n\n"

        # ── Confidence scoring ──
        "== CONFIDENCE SCORING ==\n"
        "confidence is a float 0.0–1.0. Calculate it systematically:\n"
        "- Start at 0.5 (neutral).\n"
        "- +0.10 if mtf_synthesis.alignment = ALIGNED.\n"
        "- +0.05 per timeframe with confluence.score >= 70.\n"
        "- +0.10 if market_regime = TRENDING_UP/DOWN (matching direction).\n"
        "- +0.05 if RSI in zone matching direction (not overbought for BUY, not oversold for SELL).\n"
        "- -0.10 if any higher timeframe (H4/D1) conflicts with signal direction.\n"
        "- -0.15 if volatility.squeeze = true on M1 (breakout imminent, direction unclear).\n"
        "- -0.05 if spread_points > 30.\n"
        "If final confidence < constraints.required_confidence → action=HOLD.\n\n"

        # ── SL/TP rules ──
        "== SL/TP RULES (for BUY/SELL only) ==\n"
        "entry_price: use extra.ask for BUY, extra.bid for SELL.\n"
        "sl_price: place at nearest support/resistance from key_levels, "
        "OR use 1.5× ATR from entry (whichever is tighter but >= 1.0× ATR).\n"
        "tp_price: minimum Risk:Reward ratio of 1.5:1 (tp distance >= 1.5 × sl distance). "
        "Use next pivot/fibonacci level as target when possible.\n"
        "Never set SL tighter than the current spread.\n\n"

        # ── JSON output schema ──
        "== REQUIRED JSON OUTPUT ==\n"
        '{"action": "BUY|SELL|HOLD|EXIT", '
        '"confidence": 0.0-1.0, '
        '"reason": "brief 1-sentence explanation", '
        '"entry_price": number (only if BUY/SELL), '
        '"sl_price": number (only if BUY/SELL), '
        '"tp_price": number (only if BUY/SELL)}'
    )

    def decide_autonomous(self, payload: dict) -> dict:
        if not self.groq.is_configured():
            raise RuntimeError("GROQ_API_KEY manquant ou non configuré")

        result = self.groq.chat_json(
            system_prompt=self.SYSTEM_PROMPT,
            user_payload=payload,
            timeout=20,
            max_tokens=300,
        )

        if not isinstance(result, dict):
            raise RuntimeError("Réponse Groq invalide (JSON attendu)")

        return result


app = Flask(__name__)
ai_engine = AdaptiveAIEngine()
logger = logging.getLogger("AIEngine")


@app.route("/")
def index():
    return jsonify({
        "service": "AI Engine - Groq",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "AI Engine"})


@app.route("/api/health")
def api_health():
    return health()


@app.route("/api/decision", methods=["POST"])
@require_api_token
def decision_api():
    try:
        payload = request.get_json() or {}
        decision = ai_engine.decide_autonomous(payload)
        if isinstance(decision, dict):
            logger.info(
                "IA decision | symbol=%s | action=%s | confidence=%s",
                payload.get("symbol"),
                decision.get("action"),
                decision.get("confidence"),
            )
        return jsonify(decision)
    except Exception as e:
        return jsonify({"error": str(e)}), 503


@app.route("/api/signal")
def get_signal():
    return jsonify({"error": "endpoint disabled"}), 410


@app.route("/api/analyze", methods=["POST"])
def analyze_market_api():
    return jsonify({"error": "endpoint disabled"}), 410


def run_ai_server():
    print("=" * 50)
    print("[IA] MOTEUR IA GROQ - AUTONOME")
    print("[WEB] Serveur: http://127.0.0.1:5003")
    print("[SEC] Écoute restreinte à localhost + API token")
    print("=" * 50)
    try:
        from waitress import serve
        serve(app, host="127.0.0.1", port=5003)
        return
    except Exception:
        pass

    try:
        from wsgiref.simple_server import make_server
        httpd = make_server("127.0.0.1", 5003, app)
        httpd.serve_forever()
    except Exception:
        app.run(host="127.0.0.1", port=5003, debug=False, use_reloader=False)


if __name__ == "__main__":
    run_ai_server()