from __future__ import annotations
from Includes.performance_models import PerformanceScores


class PerformanceScoringMixin:
    def get_current_scores(
        self,
        selected_test_files: list[str] | None = None,
    ) -> PerformanceScores:
        """
        Returneaza setul curent de scoruri pentru fisierele de test selectate.

        Regula noua:
        - calculam intai pytest
        - daca pytest nu este curat, nu mai rulam coverage si mutmut
        - astfel evitam costuri mari pentru propuneri care oricum nu pot fi acceptate
        """
        pytest_score = self.run_pytest_score(selected_test_files)

        if pytest_score <= 0.0:
            return PerformanceScores(
                pytest_score=pytest_score,
                coverage_score=0.0,
                mutation_score=0.0,
            )

        if pytest_score < 100.0:
            return PerformanceScores(
                pytest_score=pytest_score,
                coverage_score=0.0,
                mutation_score=0.0,
            )

        return PerformanceScores(
            pytest_score=pytest_score,
            coverage_score=self.run_branch_coverage_score(selected_test_files),
            mutation_score=self.run_mutation_score(selected_test_files),
        )

    def get_current_scores_tuple(self) -> tuple[float, float, float]:
        """
        Metoda de compatibilitate cu stilul vechi din AutoTesting.py.
        """
        scores = self.get_current_scores()
        return (
            scores.pytest_score,
            scores.coverage_score,
            scores.mutation_score,
        )

    def has_improvement(
        self,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
    ) -> bool:
        """
        Returneaza True daca exista cel putin o imbunatatire intre cele doua
        seturi de scoruri.
        """
        return any(
            after > before
            for before, after in zip(
                (
                    before_scores.pytest_score,
                    before_scores.coverage_score,
                    before_scores.mutation_score,
                ),
                (
                    after_scores.pytest_score,
                    after_scores.coverage_score,
                    after_scores.mutation_score,
                ),
            )
        )

    def has_non_regressive_improvement(
        self,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
    ) -> bool:
        """
        Returneaza True doar daca:
        - niciun scor nu scade
        - cel putin un scor creste

        Asta previne acceptarea unor teste care cresc un scor,
        dar deterioreaza altul.
        """
        before_values = (
            before_scores.pytest_score,
            before_scores.coverage_score,
            before_scores.mutation_score,
        )
        after_values = (
            after_scores.pytest_score,
            after_scores.coverage_score,
            after_scores.mutation_score,
        )

        has_any_decrease = any(after < before for before, after in zip(before_values, after_values))
        has_any_increase = any(after > before for before, after in zip(before_values, after_values))

        return (not has_any_decrease) and has_any_increase

    def is_pytest_clean(self, scores: PerformanceScores) -> bool:
        """
        Returneaza True doar daca suita curenta nu are teste picate la pytest.

        In modelul actual, asta inseamna pytest_score >= 100.0.
        """
        return scores.pytest_score >= 100.0

    def has_strict_improvement(
        self,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
    ) -> bool:
        """
        Returneaza True doar daca:
        - suita era curata inainte (pytest 100%)
        - suita ramane curata dupa (pytest 100%)
        - niciun scor nu scade
        - cel putin un scor creste

        Aceasta regula previne acceptarea unor teste care par sa imbunatateasca
        anumite scoruri, dar introduc teste gresite logic si strica suita.
        """
        if not self.is_pytest_clean(before_scores):
            return False

        if not self.is_pytest_clean(after_scores):
            return False

        before_values = (
            before_scores.pytest_score,
            before_scores.coverage_score,
            before_scores.mutation_score,
        )
        after_values = (
            after_scores.pytest_score,
            after_scores.coverage_score,
            after_scores.mutation_score,
        )

        has_any_decrease = any(
            after < before for before, after in zip(before_values, after_values)
        )
        has_any_increase = any(
            after > before for before, after in zip(before_values, after_values)
        )

        return (not has_any_decrease) and has_any_increase

    def has_improvement_from_tuples(
        self,
        before_scores: tuple[float, float, float],
        after_scores: tuple[float, float, float],
    ) -> bool:
        """
        Metoda de compatibilitate pentru cod care lucreaza inca pe tuple.
        """
        return any(after > before for before, after in zip(before_scores, after_scores))

    def format_improvement(
        self,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
    ) -> str:
        """
        Formateaza textual imbunatatirea dintre doua seturi de scoruri, in stil
        compatibil cu logica existenta a framework-ului.
        """
        return (
            f"Pytest: {before_scores.pytest_score}% -> {after_scores.pytest_score}%; "
            f"Branch coverage: {before_scores.coverage_score}% -> {after_scores.coverage_score}%; "
            f"Mutmut: {before_scores.mutation_score}% -> {after_scores.mutation_score}%."
        )

    def format_improvement_from_tuples(
        self,
        before_scores: tuple[float, float, float],
        after_scores: tuple[float, float, float],
    ) -> str:
        """
        Metoda de compatibilitate pentru cod care lucreaza inca pe tuple.
        """
        pytest_before, coverage_before, mutation_before = before_scores
        pytest_after, coverage_after, mutation_after = after_scores

        return (
            f"Pytest: {pytest_before}% -> {pytest_after}%; "
            f"Branch coverage: {coverage_before}% -> {coverage_after}%; "
            f"Mutmut: {mutation_before}% -> {mutation_after}%."
        )

    def format_scores_for_debug(self, scores: PerformanceScores) -> str:
        """
        Returneaza un text scurt pentru afisarea scorurilor curente in debug.
        """
        return (
            f"pytest: {scores.pytest_score}%, "
            f"coverage: {scores.coverage_score}%, "
            f"mutmut: {scores.mutation_score}%"
        )

    def explain_rejection_reason(
        self,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
    ) -> str:
        """
        Returneaza un mesaj scurt care explica de ce o propunere nu trece
        criteriul strict de acceptare.
        """
        if not self.is_pytest_clean(before_scores):
            return (
                "Suita curenta nu este complet valida la pytest, deci nu se poate "
                "folosi criteriul strict de acceptare pana nu sunt eliminate testele gresite existente."
            )

        if not self.is_pytest_clean(after_scores):
            return (
                "Propunerea este respinsa deoarece dupa adaugare suita nu mai este curata la pytest."
            )

        before_values = (
            before_scores.pytest_score,
            before_scores.coverage_score,
            before_scores.mutation_score,
        )
        after_values = (
            after_scores.pytest_score,
            after_scores.coverage_score,
            after_scores.mutation_score,
        )

        has_any_decrease = any(
            after < before for before, after in zip(before_values, after_values)
        )
        has_any_increase = any(
            after > before for before, after in zip(before_values, after_values)
        )

        if has_any_decrease:
            return (
                "Propunerea este respinsa deoarece scade cel putin un scor."
            )

        if not has_any_increase:
            return (
                "Propunerea este respinsa deoarece nu imbunatateste niciun scor."
            )

        return "Propunerea poate fi acceptata."

    def has_any_tests(
        self,
        selected_test_files: list[str] | None = None,
    ) -> bool:
        """
        Returneaza True daca exista cel putin un fisier selectat care contine
        cel putin o functie de test rulabila.
        """
        test_files = self._get_runnable_test_files(selected_test_files)
        return len(test_files) > 0
