from __future__ import annotations

from Includes.response_cleaning import ResponseCleaningMixin
from Includes.response_metadata import ResponseMetadataMixin
from Includes.response_models import ParsedResponse


class ResponseParser(
    ResponseCleaningMixin,
    ResponseMetadataMixin,
):
    """Extrage functia de test si metadatele din raspunsul modelului."""

    def __init__(self) -> None:
        self.comment_prefixes = (
            "# Rule:",
            "# Reasoning:",
            "# Explanation:",
        )
        # Markeri care indica inceputul unor sectiuni explicative nedorite
        # dupa codul Python. Sunt folositi de ResponseCleaningMixin.
        self.stop_markers = (
            "\nExplanation:",
            "\nReasoning:",
            "\nHere is",
            "\nThis test",
            "\nThe test",
            "\n```",
        )


__all__ = ["ParsedResponse", "ResponseParser"]
