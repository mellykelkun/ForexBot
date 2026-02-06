"""
CERVEAU ÉVOLUTIF - Version Groq (IA distante)
Remplace le modèle local TensorFlow pour réduire CPU/GPU.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime
from typing import Dict, List
import random

from backend.ai.groq_service import GroqService

brain_instance = None


def get_brain_instance():
    """Retourne l'instance unique du cerveau évolutif"""
    global brain_instance
    if brain_instance is None:
        brain_instance = EvolutionaryBrain()
        print("🧠 Instance unique du cerveau Groq créée")
    return brain_instance


class EvolutionaryBrain:
    def __init__(self):
        self.exit_experiences = deque(maxlen=5000)
        self.exit_memory_size = 0
        self.learning_rate = 0.001
        self.groq = GroqService()

    def predict_exit_probability(self, state: Dict) -> float:
        """Prédit la probabilité de sortie pour une position via Groq."""
        try:
            if not state:
                return 0.5

            if not self.groq.is_configured():
                raise RuntimeError("GROQ_API_KEY manquant ou non configuré")

            system_prompt = (
                "Tu es un moteur de trading. Retourne un JSON strict avec: "
                "{exit_probability: nombre entre 0 et 1}."
            )

            result = self.groq.chat_json(
                system_prompt=system_prompt,
                user_payload={"state": state},
                timeout=8,
                temperature=0.1,
                max_tokens=120,
            )

            if result and "exit_probability" in result:
                prob = float(result["exit_probability"])
                return max(0.0, min(1.0, prob))

            raise RuntimeError("Réponse Groq invalide")
        except Exception as e:
            raise RuntimeError(f"Erreur Groq: {e}")

    def extract_exit_features(self, state: Dict) -> List[float]:
        """Extrait des features simples (compatibilité)."""
        try:
            entry_price = state.get('entry_price', 0)
            current_price = state.get('current_price', 0)

            if entry_price > 0:
                if state.get('position_type') == 'BUY':
                    unrealized_pnl_pct = (current_price - entry_price) / entry_price
                else:
                    unrealized_pnl_pct = (entry_price - current_price) / entry_price
            else:
                unrealized_pnl_pct = 0

            position_age = state.get('position_age', 0)
            rsi = state.get('rsi', 50) / 100.0
            macd = state.get('macd', 0)
            volatility = min(state.get('volatility', 0.05) * 10, 1.0)
            momentum = state.get('momentum', 0)
            position_type = 1.0 if state.get('position_type') == 'BUY' else 0.0
            candle_patterns_count = len(state.get('candle_patterns', [])) / 10.0
            spread = min(state.get('spread', 0) * 1000, 1.0)

            features = [
                unrealized_pnl_pct * 100,
                position_age / 60.0,
                rsi,
                macd,
                volatility,
                momentum,
                position_type,
                candle_patterns_count,
                spread,
            ]

            return features[:9] if len(features) > 9 else features + [0.0] * (9 - len(features))
        except Exception:
            return [0.0] * 9

    def update_with_reward(self, exit_data: Dict, reward: float):
        """Enregistre l'expérience (pas d'entraînement local)."""
        try:
            state = exit_data.get('market_conditions', {})
            features = self.extract_exit_features(state)

            self.exit_experiences.append({
                'features': features,
                'reward': reward,
                'timestamp': datetime.now(),
                'exit_score': exit_data.get('exit_score', 0),
                'profit': exit_data.get('profit', 0)
            })
            self.exit_memory_size = len(self.exit_experiences)
        except Exception:
            return False

    def force_add_memory(self, count=5):
        """Compatibilité: ajoute des expériences fictives."""
        for _ in range(count):
            test_state = {
                "entry_price": random.random(),
                "current_price": random.random(),
                "position_type": random.choice(["BUY", "SELL"]),
                "rsi": random.randint(20, 80),
                "volatility": random.random(),
                "momentum": random.random(),
            }
            self.update_with_reward({"market_conditions": test_state}, random.uniform(-1, 1))
        return len(self.exit_experiences)

    def reset_memory(self):
        """Réinitialise la mémoire"""
        self.exit_experiences.clear()
        self.exit_memory_size = 0
