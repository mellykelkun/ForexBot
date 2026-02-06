"""Groq service wrapper (OpenAI-compatible API)."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv


class GroqService:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: str = "https://api.groq.com/openai/v1",
        logger: Optional[logging.Logger] = None,
    ) -> None:
        load_dotenv()
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.base_url = base_url.rstrip("/")
        self.logger = logger or logging.getLogger("GroqService")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def chat_json(
        self,
        system_prompt: str,
        user_payload: Dict[str, Any],
        timeout: int = 20,
        temperature: float = 0.2,
        max_tokens: int = 200,
    ) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            self.logger.warning("GROQ_API_KEY manquant")
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload)},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        attempts = 3
        for i in range(attempts):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                if response.status_code != 200:
                    # Retry sans response_format si JSON échoue
                    if "json_validate_failed" in response.text:
                        payload_no_format = {
                            **payload,
                            "messages": [
                                {"role": "system", "content": system_prompt + "\nRetourne uniquement un JSON valide."},
                                {"role": "user", "content": json.dumps(user_payload)},
                            ],
                        }
                        payload_no_format.pop("response_format", None)
                        retry = requests.post(url, headers=headers, json=payload_no_format, timeout=timeout)
                        if retry.status_code == 200:
                            data = retry.json()
                            content = data["choices"][0]["message"]["content"]
                            return self._safe_json_parse(content)
                    self.logger.warning(
                        "Groq error %s: %s", response.status_code, response.text[:200]
                    )
                    return None

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                return self._safe_json_parse(content)
            except Exception as exc:
                if i < attempts - 1:
                    time.sleep(0.8 * (i + 1))
                    continue
                self.logger.warning("Groq request failed: %s", exc)
                return None

    def _safe_json_parse(self, content: str) -> Optional[Dict[str, Any]]:
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
