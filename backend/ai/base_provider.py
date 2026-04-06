"""Interface abstraite pour tous les providers IA (OpenAI-compatible)."""

from __future__ import annotations

import json
import logging
import re
import time
from abc import ABC
from typing import Any, Dict, Optional

import requests


class BaseAIProvider(ABC):
    """Classe de base pour les fournisseurs IA utilisant l'API OpenAI-compatible."""

    def __init__(
        self,
        api_key: Optional[str],
        model: str,
        base_url: str,
        provider_name: str,
        logger: Optional[logging.Logger] = None,
        supports_json_mode: bool = True,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.provider_name = provider_name
        self.supports_json_mode = supports_json_mode
        self.logger = logger or logging.getLogger(f"AI:{provider_name}")

    @property
    def model_name(self) -> str:
        return self.model

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def info(self) -> Dict[str, Any]:
        """Retourne les infos publiques du provider (sans clé API)."""
        return {
            "provider": self.provider_name,
            "model": self.model,
            "configured": self.is_configured(),
            "base_url": self.base_url,
        }

    def chat_json(
        self,
        system_prompt: str,
        user_payload: Dict[str, Any],
        timeout: int = 20,
        temperature: float = 0.2,
        max_tokens: int = 300,
    ) -> Optional[Dict[str, Any]]:
        """Envoie une requête chat et parse le JSON de la réponse."""
        if not self.api_key:
            self.logger.warning("%s API key manquante", self.provider_name)
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload)},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if self.supports_json_mode:
            payload["response_format"] = {"type": "json_object"}

        attempts = 3
        for i in range(attempts):
            try:
                response = requests.post(
                    url, headers=headers, json=payload, timeout=timeout
                )
                if response.status_code != 200:
                    # Retry sans response_format si JSON échoue
                    if "json_validate_failed" in response.text and self.supports_json_mode:
                        payload_no_format: Dict[str, Any] = {
                            **payload,
                            "messages": [
                                {
                                    "role": "system",
                                    "content": system_prompt
                                    + "\nRetourne uniquement un JSON valide.",
                                },
                                {"role": "user", "content": json.dumps(user_payload)},
                            ],
                        }
                        payload_no_format.pop("response_format", None)
                        retry = requests.post(
                            url,
                            headers=headers,
                            json=payload_no_format,
                            timeout=timeout,
                        )
                        if retry.status_code == 200:
                            data = retry.json()
                            content = data["choices"][0]["message"]["content"]
                            return self._safe_json_parse(content)
                    self.logger.warning(
                        "%s error %s: %s",
                        self.provider_name,
                        response.status_code,
                        response.text[:200],
                    )
                    return None

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return self._safe_json_parse(content)

            except Exception as exc:
                if i < attempts - 1:
                    time.sleep(0.8 * (i + 1))
                    continue
                self.logger.warning(
                    "%s request failed: %s", self.provider_name, exc
                )
                return None

    @staticmethod
    def _safe_json_parse(content: str) -> Optional[Dict[str, Any]]:
        """Parse JSON avec fallback regex."""
        try:
            return json.loads(content)
        except Exception:
            match = re.search(r"\{.*\}", content, re.DOTALL)
            if not match:
                return None
            try:
                return json.loads(match.group(0))
            except Exception:
                return None
