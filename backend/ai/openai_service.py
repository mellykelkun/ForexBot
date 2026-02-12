"""OpenAI GPT provider (API OpenAI native)."""

from __future__ import annotations

import logging
import os
from typing import Optional

from dotenv import load_dotenv

from backend.ai.base_provider import BaseAIProvider


class OpenAIService(BaseAIProvider):
    """Provider pour les modèles OpenAI (GPT-4o, GPT-4o-mini, etc.)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        load_dotenv()
        super().__init__(
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            model=model or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            base_url="https://api.openai.com/v1",
            provider_name="openai",
            logger=logger,
            supports_json_mode=True,
        )
