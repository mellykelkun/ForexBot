"""Ollama provider — modèles locaux via API OpenAI-compatible."""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv

from backend.ai.base_provider import BaseAIProvider


class OllamaService(BaseAIProvider):
    """Provider pour les modèles locaux Ollama (GLM, LLaMA, Mistral, etc.)."""

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        load_dotenv()
        _base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        super().__init__(
            api_key="ollama",  # placeholder — Ollama n'exige pas de clé
            model=model or os.getenv("OLLAMA_MODEL", "glm-5:cloud"),
            base_url=_base_url,
            provider_name="ollama",
            logger=logger,
            supports_json_mode=False,  # glm-5:cloud ne supporte pas response_format
        )
        # Cache pour is_configured() — évite un appel réseau à chaque /api/providers
        self._configured_cache: Optional[bool] = None
        self._configured_cache_ts: float = 0.0
        self._configured_cache_ttl: float = 30.0  # re-vérifier toutes les 30s

    def is_configured(self) -> bool:
        """Ollama est considéré configuré si le serveur est joignable (résultat caché 30s)."""
        import requests as _req
        now = time.time()
        if self._configured_cache is not None and (now - self._configured_cache_ts) < self._configured_cache_ttl:
            return self._configured_cache
        try:
            resp = _req.get(
                self.base_url.replace("/v1", "") + "/api/tags",
                timeout=2,
            )
            self._configured_cache = resp.status_code == 200
        except Exception:
            self._configured_cache = False
        self._configured_cache_ts = now
        return self._configured_cache

    def info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self.model,
            "configured": self.is_configured(),
            "base_url": self.base_url,
            "local": True,
        }

    def chat_json(
        self,
        system_prompt: str,
        user_payload: Dict[str, Any],
        timeout: int = 120,
        temperature: float = 0.2,
        max_tokens: int = 300,
    ) -> Optional[Dict[str, Any]]:
        """Requête via l'API native Ollama (/api/chat) pour modèles raisonneurs."""
        import re
        import requests as _req

        # API native Ollama — gère mieux les modèles raisonneurs que /v1
        native_url = self.base_url.replace("/v1", "") + "/api/chat"

        # Les modèles raisonneurs (glm-5, deepseek-r1…) consomment beaucoup
        # de tokens en thinking avant de produire le content.
        # num_predict doit couvrir thinking + réponse finale.
        num_predict = max(max_tokens * 12, 4000)

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                    + "\nRéponds UNIQUEMENT avec un objet JSON brut.",
                },
                {"role": "user", "content": json.dumps(user_payload)},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": num_predict,
            },
        }

        attempts = 3
        for i in range(attempts):
            try:
                response = _req.post(
                    native_url, json=payload, timeout=timeout,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code != 200:
                    self.logger.warning(
                        "ollama error %s: %s",
                        response.status_code,
                        response.text[:200],
                    )
                    if i < attempts - 1:
                        time.sleep(1.0 * (i + 1))
                        continue
                    return None

                data = response.json()
                msg = data.get("message", {})
                content = (msg.get("content") or "").strip()

                # Modèles raisonneurs: fallback sur thinking si content vide
                if not content:
                    thinking = (msg.get("thinking") or "").strip()
                    if thinking:
                        # Extraire le dernier bloc JSON du raisonnement
                        json_match = re.findall(r'\{[^{}]*\}', thinking)
                        if json_match:
                            content = json_match[-1]

                if not content:
                    self.logger.warning("ollama: réponse vide (tentative %d/%d)", i + 1, attempts)
                    if i < attempts - 1:
                        time.sleep(1.0 * (i + 1))
                        continue
                    return None

                return self._safe_json_parse(content)

            except Exception as exc:
                if i < attempts - 1:
                    time.sleep(1.0 * (i + 1))
                    continue
                self.logger.warning("ollama request failed: %s", exc)
                return None
