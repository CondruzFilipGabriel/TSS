from __future__ import annotations
from dataclasses import dataclass


@dataclass
class PerformanceScores:
    """Scorurile folosite pentru compararea suitelor de teste."""

    pytest_score: float
    coverage_score: float
    mutation_score: float
    pytest_output: str = ""
    coverage_output: str = ""
    mutation_output: str = ""
