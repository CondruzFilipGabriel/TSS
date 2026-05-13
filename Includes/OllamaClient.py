from __future__ import annotations

from typing import Optional

from Includes.Config import AppConfig
from Includes.Logger import Logger
from Includes.ollama_http import OllamaHttpMixin
from Includes.ollama_process import OllamaProcessMixin
from Includes.ollama_generation import OllamaGenerationMixin
from Includes.ollama_models import OllamaResponse


class OllamaClient(
    OllamaHttpMixin,
    OllamaProcessMixin,
    OllamaGenerationMixin,
):
    """Client minim pentru pornirea Ollama si generarea raspunsurilor."""

    def __init__(
        self,
        config: AppConfig,
        logger: Logger,
    ) -> None:
        self.config = config
        self.logger = logger
        # Procesul local Ollama pornit de framework, daca API-ul nu era deja activ.
        # Numele acestor atribute este folosit de OllamaProcessMixin.
        self._ollama_process: Optional[object] = None
        self._started_by_framework = False


__all__ = ["OllamaClient", "OllamaResponse"]
