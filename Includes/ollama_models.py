from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OllamaResponse:
    """Raspunsul brut primit de la Ollama si metadatele generarii."""

    text: str
    duration_sec: float
    model: str = ""
