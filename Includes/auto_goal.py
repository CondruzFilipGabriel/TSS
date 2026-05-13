from __future__ import annotations
from pathlib import Path

from Includes.performance_models import PerformanceScores


class AutoGoalMixin:
    """
    Helper pentru oprirea automata a fluxului cand o categorie a atins
    scorurile maxime.

    Criteriul folosit in framework este:
    - pytest 100%
    - coverage 100%
    - mutmut 100%

    Verificarea se face pe categoria curenta, adica pe fisierul test_<categorie>.py
    asociat fisierului testing_<categorie>.md.
    """

    def is_maximum_score(self, scores: PerformanceScores) -> bool:
        """
        Returneaza True cand toate scorurile relevante sunt la 100%.
        """
        return (
            scores.pytest_score >= 100.0
            and scores.coverage_score >= 100.0
            and scores.mutation_score >= 100.0
        )

    def log_maximum_score_if_reached(
        self,
        category: str,
        scores: PerformanceScores,
    ) -> bool:
        """
        Logheaza explicit atingerea scorului maxim si returneaza verdictul.
        """
        if not self.is_maximum_score(scores):
            return False

        self.logger.console_step(
            f"categoria {category} a atins 100% pytest, 100% coverage si 100% mutmut"
        )
        self.logger.debug(
            f"Oprire pentru categoria {category}: "
            f"{self.format_scores_for_debug(scores)}."
        )
        return True

    def get_scores_for_category(self, testing_md_path: Path) -> PerformanceScores:
        """
        Calculeaza scorurile pentru fisierul de test asociat unei categorii.
        """
        test_file_path = self.workspace.map_testing_md_to_test_py(testing_md_path)
        return self.get_current_scores([test_file_path.name])

    def is_category_complete(self, testing_md_path: Path) -> bool:
        """
        Verifica daca o categorie este deja completa si poate fi sarita.
        """
        category = self.workspace.get_category_name_from_testing_md(testing_md_path)
        test_file_path = self.workspace.map_testing_md_to_test_py(testing_md_path)
        selected_test_files = [test_file_path.name]

        if not self.tests_performance.has_any_tests(selected_test_files):
            return False

        scores = self.get_current_scores(selected_test_files)
        return self.log_maximum_score_if_reached(category, scores)

    def are_all_categories_complete(self) -> bool:
        """
        Verifica daca toate categoriile existente au atins scorurile maxime.
        """
        if not self.fisiere_testing_md:
            return False

        for testing_md_path in self.fisiere_testing_md:
            if not self.is_category_complete(testing_md_path):
                return False

        self.logger.console_step(
            "toate categoriile au atins 100% pytest, 100% coverage si 100% mutmut"
        )
        return True
