"""
MOTEUR IA – Multi-Provider (Groq / OpenAI / DeepSeek)
Switching dynamique en temps réel depuis le dashboard.
Même SYSTEM_PROMPT partagé par tous les providers.
Sécurisé: écoute 127.0.0.1 uniquement + token API.
"""

from datetime import datetime

import logging
from flask import Flask, jsonify, request

from backend.ai.provider_manager import AIProviderManager
from backend.security.auth import require_api_token


class AdaptiveAIEngine:
    def __init__(self):
        self.provider_manager = AIProviderManager()

    # ── System prompt (English for better LLM performance) ─────────────
    SYSTEM_PROMPT = (
        "You are an autonomous trading decision engine. "
        "You are the SOLE decision-maker. Every trade outcome — profit or loss — "
        "is a DIRECT consequence of YOUR decisions. "
        "Return ONLY a strict JSON object — no prose, no markdown.\n\n"

        # ── YOUR ACCOUNTABILITY ──
        "== YOUR ACCOUNTABILITY ==\n"
        "You receive your own recent trade history in 'my_trade_history'. "
        "This shows YOUR past decisions and their results. Study them CAREFULLY:\n"
        "- If you see consecutive losses → your analysis was WRONG. Be MORE selective.\n"
        "- If most losses are 'stop_loss' hits → your entry timing or SL placement was bad.\n"
        "- If win_rate < 40% → you are taking LOW-QUALITY signals. ONLY trade the BEST setups.\n"
        "- If avg_loss > avg_win → your risk:reward is inverted. Widen TP or tighten SL.\n"
        "- If net_pnl is negative → you are LOSING the account's money. Switch to HOLD "
        "until you identify a TRULY high-probability setup with confluence >= 85.\n"
        "- AFTER a losing streak (2+ losses), require ALL of these before any BUY/SELL:\n"
        "  * mtf_synthesis.alignment = ALIGNED\n"
        "  * At least 4 timeframes with confluence.score >= 75\n"
        "  * confidence >= 0.90\n"
        "  * RSI not in overbought/oversold extreme zone\n"
        "  * No squeeze on any timeframe\n"
        "DO NOT repeat the same mistakes. If a pattern/setup caused a loss, avoid it.\n\n"

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
        "extra: contains bid, ask, spread_points, and constraints.\n"
        "my_trade_history: YOUR past trade results. Contains:\n"
        "  - recent_trades: list of last 5 closed trades with profit, close_reason "
        "(stop_loss/take_profit/manual), type, volume, time.\n"
        "  - stats: total trades, wins, losses, win_rate_pct, net_pnl, avg_win, avg_loss, "
        "sl_hit_count, tp_hit_count, current_streak.\n"
        "ANALYZE my_trade_history BEFORE making any decision.\n\n"

        # ── Decision rules ──
        "== DECISION RULES ==\n"
        "1. DEFAULT is HOLD. Only output BUY or SELL when ALL of these are true:\n"
        "   a) mtf_synthesis.alignment = ALIGNED (most timeframes agree).\n"
        "   b) At least 3 timeframes show confluence.score >= 70.\n"
        "   c) M1 AND M5 momentum BOTH align with the higher-timeframe trend.\n"
        "   d) market_regime is TRENDING_UP or TRENDING_DOWN (not RANGING) on at least 3 TFs.\n"
        "   e) No conflicting candle_patterns (e.g. reversal pattern against trend).\n"
        "   f) H4 and D1 trend direction MUST agree with the signal direction.\n"
        "   g) RSI on M5 must be between 35-65 (not in extreme zones).\n"
        "2. If context='exit': action ∈ {EXIT, HOLD}. EXIT when reversal signals appear "
        "or profit target zone reached.\n"
        "3. QUALITY OVER QUANTITY: It is ALWAYS better to HOLD and miss a trade than to "
        "take a bad trade and lose money. Your job is capital PRESERVATION first.\n\n"

        # ── Self-correction rules ──
        "== SELF-CORRECTION (based on my_trade_history) ==\n"
        "Apply these adjustments based on your recent performance:\n"
        "- If current_streak contains '1+ consecutive losses' → add +0.15 to min confidence.\n"
        "- If current_streak contains '2+ consecutive losses' → ONLY output HOLD "
        "unless confluence.score >= 85 on 4+ timeframes.\n"
        "- If current_streak contains '3+ consecutive losses' → ALWAYS output HOLD. "
        "Do NOT trade until the streak is broken by other means.\n"
        "- If win_rate_pct < 60% → require confluence.score >= 80 on ALL timeframes "
        "showing a signal.\n"
        "- If sl_hit_count > tp_hit_count → your SL is too tight. "
        "Place SL at 2.5× ATR minimum (not 1.5×).\n"
        "- If most losses are on the SAME pair → consider HOLD for that pair until "
        "the market regime changes.\n"
        "EXPLAIN in 'reason' what you learned from recent losses if applicable.\n\n"

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
        "- +0.05 per timeframe with confluence.score >= 75 (max +0.25 for 5 TFs).\n"
        "- +0.10 if market_regime = TRENDING_UP/DOWN on 3+ timeframes (matching direction).\n"
        "- +0.05 if RSI on ALL timeframes is in safe zone (30-70).\n"
        "- +0.05 if H4 AND D1 both confirm direction.\n"
        "- -0.15 if any higher timeframe (H4/D1) conflicts with signal direction.\n"
        "- -0.20 if volatility.squeeze = true on ANY timeframe (breakout imminent, direction unclear).\n"
        "- -0.10 if spread_points > 20.\n"
        "- -0.15 if my_trade_history.stats.win_rate_pct < 50% (you're underperforming).\n"
        "- -0.10 per consecutive loss in current_streak.\n"
        "MAXIMUM possible confidence = ~0.95. Required minimum = 0.90.\n"
        "If final confidence < constraints.required_confidence → action=HOLD.\n\n"

        # ── SL/TP rules ──
        "== SL/TP RULES (for BUY/SELL only) ==\n"
        "entry_price: use extra.ask for BUY, extra.bid for SELL.\n"
        "sl_price: place at nearest support/resistance from key_levels, "
        "OR use 2.0× ATR from entry (whichever is tighter but >= 1.5× ATR). "
        "If my_trade_history shows sl_hit_count > tp_hit_count, use 2.5× ATR minimum.\n"
        "tp_price: minimum Risk:Reward ratio of 2.0:1 (tp distance >= 2.0 × sl distance). "
        "Use next pivot/fibonacci level as target when possible.\n"
        "Never set SL tighter than the current spread.\n\n"

        # ── JSON output schema ──
        "== REQUIRED JSON OUTPUT ==\n"
        '{"action": "BUY|SELL|HOLD|EXIT", '
        '"confidence": 0.0-1.0, '
        '"reason": "brief 1-sentence explanation including self-assessment if losing", '
        '"entry_price": number (only if BUY/SELL), '
        '"sl_price": number (only if BUY/SELL), '
        '"tp_price": number (only if BUY/SELL)}'
    )

    def decide_autonomous(self, payload: dict) -> dict:
        provider = self.provider_manager.get_active()
        if not provider.is_configured():
            raise RuntimeError(
                f"Provider '{provider.provider_name}' non configuré (clé API manquante)"
            )

        result = self.provider_manager.chat_json(
            system_prompt=self.SYSTEM_PROMPT,
            user_payload=payload,
            timeout=25,
            max_tokens=400,
        )

        if not isinstance(result, dict):
            active = self.provider_manager.active_name
            raise RuntimeError(f"Réponse {active} invalide (JSON attendu)")

        return result


app = Flask(__name__)
ai_engine = AdaptiveAIEngine()
logger = logging.getLogger("AIEngine")


@app.route("/")
def index():
    provider = ai_engine.provider_manager.get_active()
    return jsonify({
        "service": f"AI Engine - {provider.provider_name.upper()}",
        "model": provider.model,
        "status": "running",
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy", "service": "AI Engine"})


@app.route("/api/health")
def api_health():
    return health()


@app.route("/api/providers")
def api_providers():
    """Liste tous les providers IA et leur statut."""
    return jsonify(ai_engine.provider_manager.get_status())


@app.route("/api/switch-provider", methods=["POST"])
@require_api_token
def api_switch_provider():
    """Change le provider IA actif en temps réel."""
    data = request.get_json() or {}
    provider_name = data.get("provider", "").strip()
    if not provider_name:
        return jsonify({"success": False, "error": "Champ 'provider' requis"}), 400
    result = ai_engine.provider_manager.switch(provider_name)
    if result["success"]:
        logger.info(
            "Provider IA changé: %s → %s", result["previous"], result["active"]
        )
    return jsonify(result), 200 if result["success"] else 400


@app.route("/api/decision", methods=["POST"])
@require_api_token
def decision_api():
    try:
        payload = request.get_json() or {}
        decision = ai_engine.decide_autonomous(payload)
        if isinstance(decision, dict):
            active = ai_engine.provider_manager.active_name
            logger.info(
                "IA decision | provider=%s | symbol=%s | action=%s | confidence=%s",
                active,
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
    status = ai_engine.provider_manager.get_status()
    configured = [p["provider"] for p in status["providers"] if p["configured"]]
    print("=" * 50)
    print(f"[IA] MOTEUR IA MULTI-PROVIDER — AUTONOME")
    print(f"[IA] Actif: {status['active_provider'].upper()} ({status['active_model']})")
    print(f"[IA] Configurés: {configured}")
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