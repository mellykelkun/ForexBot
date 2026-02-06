"""
MOTEUR IA - Groq uniquement (IA autonome)
Tout traitement local/heuristique supprimé.
"""

from datetime import datetime

import logging
from flask import Flask, jsonify, request

from backend.ai.groq_service import GroqService


class AdaptiveAIEngine:
    def __init__(self):
        self.groq = GroqService()

    def decide_autonomous(self, payload: dict) -> dict:
        if not self.groq.is_configured():
            raise RuntimeError("GROQ_API_KEY manquant ou non configuré")

        prompt = (
            "Tu es un moteur de trading autonome. Retourne uniquement un JSON strict (pas de texte). "
            "Clés obligatoires: action, confidence, reason. "
            "Si context='entry': action ∈ {BUY, SELL, HOLD}. "
            "Si action BUY/SELL: inclure entry_price, sl_price, tp_price (nombres). "
            "Si context='exit': action ∈ {EXIT, HOLD}. "
            "Respecte strictement les contraintes si présentes dans payload.constraints et payload.trade_state : "
            "- si trade_state.last_trade_seconds_ago < constraints.min_seconds_between_trades => action=HOLD. "
            "- si trade_state.trades_last_hour >= constraints.max_trades_per_hour => action=HOLD. "
            "- si trade_state.trades_last_day >= constraints.max_trades_per_day => action=HOLD. "
            "- si confidence < constraints.required_confidence => action=HOLD. "
            "Analyse aussi les indicateurs et chandeliers si présents dans payload.indicators (M1/M5/H1/H4). "
            "Favorise HOLD par défaut et n'envoie BUY/SELL que si signal fort et clair."
        )

        result = self.groq.chat_json(
            system_prompt=prompt,
            user_payload=payload,
            timeout=20,
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
    print("[WEB] Serveur: http://localhost:5003")
    print("=" * 50)
    try:
        from waitress import serve
        serve(app, host="0.0.0.0", port=5003)
        return
    except Exception:
        pass

    try:
        from wsgiref.simple_server import make_server
        httpd = make_server("0.0.0.0", 5003, app)
        httpd.serve_forever()
    except Exception:
        app.run(host="0.0.0.0", port=5003, debug=False, use_reloader=False)


if __name__ == "__main__":
    run_ai_server()