"""Gestionnaire multi-providers IA avec switching dynamique thread-safe."""

from __future__ import annotations

import logging
import os
import threading
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from backend.ai.base_provider import BaseAIProvider
from backend.ai.groq_service import GroqService
from backend.ai.openai_service import OpenAIService
from backend.ai.deepseek_service import DeepSeekService


class AIProviderManager:
    """Gère l'ensemble des providers IA et le switching en temps réel."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        load_dotenv()
        self.logger = logger or logging.getLogger("AIProviderManager")
        self._lock = threading.Lock()

        # Initialise tous les providers disponibles
        self._providers: Dict[str, BaseAIProvider] = {
            "groq": GroqService(),
            "openai": OpenAIService(),
            "deepseek": DeepSeekService(),
        }

        # Provider actif (par défaut ou depuis .env)
        default = os.getenv("ACTIVE_AI_PROVIDER", "groq").lower().strip()
        if default not in self._providers:
            default = "groq"
        self._active_name: str = default

        self.logger.info(
            "AIProviderManager initialisé | actif=%s | configurés=%s",
            self._active_name,
            [n for n, p in self._providers.items() if p.is_configured()],
        )

    @property
    def active_name(self) -> str:
        with self._lock:
            return self._active_name

    def get_active(self) -> BaseAIProvider:
        """Retourne le provider actif."""
        with self._lock:
            return self._providers[self._active_name]

    def switch(self, provider_name: str) -> Dict[str, Any]:
        """Change de provider en temps réel. Retourne le statut."""
        name = provider_name.lower().strip()
        if name not in self._providers:
            return {
                "success": False,
                "error": f"Provider inconnu: {name}. Disponibles: {list(self._providers.keys())}",
            }

        provider = self._providers[name]
        if not provider.is_configured():
            return {
                "success": False,
                "error": f"Provider '{name}' non configuré (clé API manquante). "
                         f"Ajoutez la variable d'environnement correspondante dans .env.",
            }

        with self._lock:
            old = self._active_name
            self._active_name = name

        self.logger.info("Provider IA changé: %s → %s (model=%s)", old, name, provider.model)
        return {
            "success": True,
            "previous": old,
            "active": name,
            "model": provider.model,
        }

    def list_providers(self) -> List[Dict[str, Any]]:
        """Liste tous les providers avec leur statut."""
        with self._lock:
            active = self._active_name

        result: List[Dict[str, Any]] = []
        for name, provider in self._providers.items():
            info = provider.info()
            info["active"] = (name == active)
            result.append(info)
        return result

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut complet du manager."""
        with self._lock:
            active = self._active_name
        provider = self._providers[active]
        return {
            "active_provider": active,
            "active_model": provider.model,
            "configured": provider.is_configured(),
            "providers": self.list_providers(),
        }

    def chat_json(
        self,
        system_prompt: str,
        user_payload: Dict[str, Any],
        timeout: int = 20,
        temperature: float = 0.2,
        max_tokens: int = 300,
    ) -> Optional[Dict[str, Any]]:
        """Délègue au provider actif."""
        provider = self.get_active()
        self.logger.debug(
            "chat_json via %s (model=%s)", provider.provider_name, provider.model
        )
        return provider.chat_json(
            system_prompt=system_prompt,
            user_payload=user_payload,
            timeout=timeout,
            temperature=temperature,
            max_tokens=max_tokens,
        )
