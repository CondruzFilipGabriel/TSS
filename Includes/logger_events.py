from __future__ import annotations

import json
from typing import Any

from Includes.performance_models import PerformanceScores


class LoggerEventsMixin:
    """
    Jurnalizare structurata pentru fluxul de generare automata.

    Fisierul logs/events.jsonl completeaza framework.log cu intrari JSON Lines
    usor de filtrat. Nu salveaza codul complet al testelor propuse; pastreaza
    doar metadate, scoruri si decizii, astfel incat jurnalul sa ramana compact.
    """

    def _events_log_file(self):
        """Returneaza calea fisierului JSONL pentru evenimentele structurale."""
        return self.config.paths.debug_dir / "events.jsonl"

    def _score_dict(self, scores: PerformanceScores | None) -> dict[str, float] | None:
        """Converteste un obiect PerformanceScores intr-un dictionar simplu."""
        if scores is None:
            return None

        return {
            "pytest": scores.pytest_score,
            "coverage": scores.coverage_score,
            "mutmut": scores.mutation_score,
        }

    def log_event(self, event_type: str, **payload: Any) -> None:
        """
        Scrie un eveniment JSONL in logs/events.jsonl.

        Evenimentele sunt active doar cand debugging-ul este activ, la fel ca
        logul tehnic principal. Astfel rularea normala ramane silentioasa.
        """
        if not self.debugging_enabled:
            return

        self._ensure_debug_directory_exists()

        entry = {
            "timestamp": self._current_timestamp(),
            "event": event_type,
            **payload,
        }

        with self._events_log_file().open("a", encoding="utf-8") as file:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def log_category_start(
        self,
        stage: str,
        category: str,
        test_file_name: str | None = None,
    ) -> None:
        """Logheaza inceputul procesarii unei categorii."""
        self.log_event(
            "category_start",
            stage=stage,
            category=category,
            test_file=test_file_name,
        )

    def log_category_skip(
        self,
        stage: str,
        category: str,
        reason: str,
        scores: PerformanceScores | None = None,
    ) -> None:
        """Logheaza sarirea unei categorii."""
        self.log_event(
            "category_skip",
            stage=stage,
            category=category,
            reason=reason,
            scores=self._score_dict(scores),
        )

    def log_subtype_start(
        self,
        category: str,
        subtype_number: int,
        total_subtypes: int,
        subtype_text: str,
    ) -> None:
        """Logheaza inceputul unui subtip predefinit."""
        self.log_event(
            "subtype_start",
            stage="initial",
            category=category,
            subtype_number=subtype_number,
            total_subtypes=total_subtypes,
            subtype=subtype_text,
        )

    def log_attempt_start(
        self,
        stage: str,
        category: str,
        attempt_number: int,
        attempts_without_progress: int,
        max_attempts_without_progress: int,
        scores_before: PerformanceScores | None = None,
        subtype_number: int | None = None,
        subtype_text: str | None = None,
        ai_budget_remaining_sec: float | None = None,
    ) -> None:
        """Logheaza inceputul unei incercari de generare."""
        self.log_event(
            "attempt_start",
            stage=stage,
            category=category,
            subtype_number=subtype_number,
            subtype=subtype_text,
            attempt_number=attempt_number,
            attempts_without_progress=attempts_without_progress,
            max_attempts_without_progress=max_attempts_without_progress,
            ai_budget_remaining_sec=ai_budget_remaining_sec,
            scores_before=self._score_dict(scores_before),
        )

    def log_attempt_invalid(
        self,
        stage: str,
        category: str,
        attempt_number: int,
        reason: str,
        subtype_number: int | None = None,
    ) -> None:
        """Logheaza o incercare fara functie valida."""
        self.log_event(
            "attempt_invalid",
            stage=stage,
            category=category,
            subtype_number=subtype_number,
            attempt_number=attempt_number,
            reason=reason,
        )

    def log_candidate_scores(
        self,
        stage: str,
        category: str,
        selected_test_files: list[str],
        scores_after: PerformanceScores,
        subtype_number: int | None = None,
    ) -> None:
        """Logheaza scorurile obtinute de candidatul curent."""
        self.log_event(
            "candidate_scores",
            stage=stage,
            category=category,
            subtype_number=subtype_number,
            selected_test_files=selected_test_files,
            scores_after=self._score_dict(scores_after),
        )

    def log_attempt_accepted(
        self,
        stage: str,
        category: str,
        function_name: str,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
        subtype_number: int | None = None,
        rule_saved: bool | None = None,
    ) -> None:
        """Logheaza acceptarea unei functii de test."""
        self.log_event(
            "attempt_accepted",
            stage=stage,
            category=category,
            subtype_number=subtype_number,
            function_name=function_name,
            scores_before=self._score_dict(before_scores),
            scores_after=self._score_dict(after_scores),
            rule_saved=rule_saved,
        )

    def log_attempt_rejected(
        self,
        stage: str,
        category: str,
        function_name: str | None,
        reason: str,
        before_scores: PerformanceScores | None = None,
        after_scores: PerformanceScores | None = None,
        subtype_number: int | None = None,
    ) -> None:
        """Logheaza respingerea unei functii de test."""
        self.log_event(
            "attempt_rejected",
            stage=stage,
            category=category,
            subtype_number=subtype_number,
            function_name=function_name,
            reason=reason,
            scores_before=self._score_dict(before_scores),
            scores_after=self._score_dict(after_scores),
        )

    def log_stagnation_stop(
        self,
        stage: str,
        category: str,
        attempts_without_progress: int,
        subtype_number: int | None = None,
    ) -> None:
        """Logheaza oprirea unei bucle din cauza stagnarii."""
        self.log_event(
            "stagnation_stop",
            stage=stage,
            category=category,
            subtype_number=subtype_number,
            attempts_without_progress=attempts_without_progress,
        )

    def log_rule_result(
        self,
        category: str,
        rule_saved: bool,
        reasoning: str,
        rule: str | None = None,
    ) -> None:
        """Logheaza daca o regula noua a fost sau nu salvata."""
        self.log_event(
            "rule_result",
            stage="discovery",
            category=category,
            rule_saved=rule_saved,
            rule=rule,
            reasoning=reasoning,
        )
