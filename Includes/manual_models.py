from __future__ import annotations
from dataclasses import dataclass


class CommandResult:
    """
    Stores the result of an external command.
    """

    command: list[str]
    returncode: int
    output: str
    timed_out: bool = False

class PytestResult:
    """
    Stores the pytest summary.
    """

    score: float
    passed: bool
    output: str

class CoverageResult:
    """
    Stores the branch coverage summary.
    """

    score: float
    output: str

class MutmutResult:
    """
    Stores the mutation testing summary.
    """

    score: float
    total_mutants: int
    killed_mutants: int
    unresolved_mutants: int
    output: str
