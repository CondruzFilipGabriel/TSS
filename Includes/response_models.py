from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ParsedResponse:
    """Rezultatul extragerii codului si metadatelor din raspunsul modelului."""

    raw_text: str
    cleaned_text: str
    function_code: str
    metadata_comments: str
    function_name: str | None = None
    rule: str = ""
    reasoning: str = ""
