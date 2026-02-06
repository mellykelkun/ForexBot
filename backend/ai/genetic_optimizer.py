"""Module désactivé: ancien optimiseur génétique supprimé (Groq uniquement)."""

def __getattr__(name):
    raise RuntimeError("genetic_optimizer désactivé: utiliser /api/decision")

class GeneticOptimizer:
    def __init__(self):
        raise RuntimeError("genetic_optimizer désactivé: utiliser /api/decision")