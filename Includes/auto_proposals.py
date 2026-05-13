from __future__ import annotations
import hashlib
from Includes.performance_models import PerformanceScores


class AutoProposalMixin:
    def compute_function_hash(self, function_code: str) -> str:
        """
        Construieste un hash stabil pentru o functie de test, astfel incat
        aceeasi propunere sa poata fi recunoscuta chiar daca difera doar prin
        whitespace minor.
        """
        normalized_code = "\n".join(
            line.rstrip()
            for line in (function_code or "").strip().splitlines()
        ).strip()

        return hashlib.sha256(normalized_code.encode("utf-8")).hexdigest()

    def get_failed_attempts_for_category(self, category: str) -> list[tuple[str, str]]:
        """
        Returneaza lista incercarilor respinse deja memorate pentru o categorie.
        """
        return list(self.failed_attempts_by_category.get(category, []))

    def remember_failed_attempt(
        self,
        category: str,
        function_code: str,
        rejection_reason: str,
        max_items_per_category: int = 25,
    ) -> None:
        """
        Memoreaza o incercare respinsa pentru a putea fi data ulterior modelului
        ca exemplu negativ.

        Duplicatele exacte (aceeasi functie + acelasi motiv) sunt ignorate.
        """
        clean_function = (function_code or "").strip()
        clean_reason = (rejection_reason or "").strip()

        if not clean_function:
            clean_function = "# Empty or unusable previous answer"

        if not clean_reason:
            clean_reason = "Rejected without an explicit recorded reason."

        bucket = self.failed_attempts_by_category.setdefault(category, [])
        candidate = (clean_function, clean_reason)

        if candidate in bucket:
            return

        bucket.append(candidate)

        if len(bucket) > max_items_per_category:
            del bucket[:-max_items_per_category]

    def has_rejected_hash(self, category: str, function_code: str) -> bool:
        """
        Verifica daca functia a mai fost respinsa deja in etapa 2 pentru categoria data.
        """
        function_hash = self.compute_function_hash(function_code)
        return function_hash in self.rejected_hashes_by_category.get(category, set())

    def remember_rejected_hash(self, category: str, function_code: str) -> None:
        """
        Salveaza hash-ul unei propuneri respinse in etapa 2, pentru a evita
        re-evaluarea aceleiasi functii.
        """
        function_hash = self.compute_function_hash(function_code)
        bucket = self.rejected_hashes_by_category.setdefault(category, set())
        bucket.add(function_hash)

    def build_candidate_selected_test_files(
        self,
        category_test_file_name: str,
    ) -> list[str]:
        """
        Returneaza lista fisierelor care trebuie evaluate pentru o propunere noua:
        - fisierul categoriei
        - fisierul temporar al propunerii

        Noua logica de acceptare trebuie sa masoare performanta pe:
        testele categoriei + propunerea noua.
        """
        return [
            category_test_file_name,
            self.config.files.proposal_test_file_name,
        ]

    def should_accept_stage2_proposal(
        self,
        category_has_tests_before: bool,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
    ) -> bool:
        """
        Decide daca o propunere din etapa 2 trebuie acceptata.

        Reguli:
        - daca categoria avea deja teste, se aplica criteriul strict actual:
        suita trebuie sa fie curata inainte si dupa, niciun scor sa nu scada,
        iar cel putin un scor sa creasca
        - daca categoria era goala, permitem bootstrap-ul:
        propunerea este acceptata daca noua suita candidat este curata la pytest
        si exista o imbunatatire reala fata de starea 0-score
        (inclusiv cresterea pytest de la 0 la 100)
        """
        if category_has_tests_before:
            return self.tests_performance.has_strict_improvement(
                before_scores=before_scores,
                after_scores=after_scores,
            )

        if not self.tests_performance.is_pytest_clean(after_scores):
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

        return any(after > before for before, after in zip(before_values, after_values))

    def explain_stage2_rejection_reason(
        self,
        category_has_tests_before: bool,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
    ) -> str:
        """
        Explica de ce o propunere din etapa 2 a fost respinsa.

        Pentru categoriile deja populate folosim explicatia existenta.
        Pentru categoriile goale folosim o explicatie de bootstrap.
        """
        if category_has_tests_before:
            return self.tests_performance.explain_rejection_reason(
                before_scores=before_scores,
                after_scores=after_scores,
            )

        if not self.tests_performance.is_pytest_clean(after_scores):
            return (
                "Propunerea este respinsa deoarece categoria era goala, iar dupa "
                "adaugarea testului candidat suita nu este curata la pytest."
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

        if not any(after > before for before, after in zip(before_values, after_values)):
            return (
                "Propunerea este respinsa deoarece nu reuseste sa stabileasca o baza "
                "mai buna pentru categorie si nu imbunatateste niciun scor."
            )

        return "Propunerea poate fi acceptata."
