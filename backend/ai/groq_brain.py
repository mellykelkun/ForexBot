"""Module désactivé: logique locale supprimée (Groq uniquement via adaptive_engine)."""

def get_brain_instance():
    raise RuntimeError("groq_brain désactivé: utiliser /api/decision")


class EvolutionaryBrain:
    def __init__(self):
        raise RuntimeError("groq_brain désactivé: utiliser /api/decision")
