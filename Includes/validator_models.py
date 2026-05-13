from __future__ import annotations
from dataclasses import dataclass
from Includes.response_models import ParsedResponse


@dataclass
class ValidationResult:
    """Rezultatul validarii unei propuneri de test."""

    is_valid: bool
    message: str
    parsed_response: ParsedResponse
