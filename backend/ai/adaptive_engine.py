"""
MOTEUR IA - Groq uniquement (IA autonome)
Tout traitement local/heuristique supprimé.
"""

from datetime import datetime

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
            "Si context='exit': action ∈ {EXIT, HOLD}."
        )

        result = self.groq.chat_json(
            system_prompt=prompt,
            user_payload=payload,
        )

        if not isinstance(result, dict):
            raise RuntimeError("Réponse Groq invalide (JSON attendu)")

        return result


app = Flask(__name__)
ai_engine = AdaptiveAIEngine()


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