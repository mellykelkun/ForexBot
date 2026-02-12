"""DeepSeek provider (API OpenAI-compatible)."""

from __future__ import annotations

import logging
import os
from typing import Optional

from dotenv import load_dotenv

from backend.ai.base_provider import BaseAIProvider


class DeepSeekService(BaseAIProvider):
    """Provider pour les modèles DeepSeek (deepseek-chat, deepseek-reasoner)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        load_dotenv()
        super().__init__(
            api_key=api_key or os.getenv("DEEPSEEK_API_KEY"),
            model=model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            base_url="https://api.deepseek.com",
            provider_name="deepseek",
            logger=logger,
            supports_json_mode=True,
        )
