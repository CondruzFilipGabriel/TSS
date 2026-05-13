from __future__ import annotations

from Includes.performance_models import PerformanceScores


class AutoReportingMixin:
    def afiseaza_rezumat_generare(self) -> None:
        """Afiseaza un rezumat scurt al testelor acceptate pe categorii."""
        generated = getattr(self, "generated_tests_by_category", {})
        if not generated:
            self.logger.console_step("teste acceptate in rularea curenta: 0")
            return

        self.logger.console_step("teste acceptate:")
        for category in sorted(generated):
            self.logger.console_step(
                f"{category}: {generated.get(category, 0)}"
            )

    def _format_final_score_line(self, label: str, scores: PerformanceScores) -> str:
        return (
            f"{label}: pytest {scores.pytest_score}%, "
            f"coverage {scores.coverage_score}%, "
            f"mutmut {scores.mutation_score}%"
        )

    def colecteaza_performanta_finala(self) -> None:
        """
        Masoara performanta finala inainte de arhivare.

        Rezultatele sunt memorate deoarece arhivarea muta fisierele test_*.py
        si to_test.py din root in folderul arh/.
        """
        self.final_scores_by_category = {}
        self.final_scores_all = None

        all_test_files: list[str] = []

        self.logger.console_step("masor performanta finala")

        for testing_md_path in self.fisiere_testing_md:
            category = self.workspace.get_category_name_from_testing_md(testing_md_path)
            test_file = self.workspace.map_testing_md_to_test_py(testing_md_path)
            selected = [test_file.name]

            if not self.tests_performance.has_any_tests(selected):
                self.logger.debug(
                    f"Categoria {category} nu are teste rulabile pentru masurarea finala."
                )
                continue

            scores = self.get_current_scores(selected)
            self.final_scores_by_category[category] = scores
            all_test_files.append(test_file.name)

        if all_test_files:
            self.final_scores_all = self.get_current_scores(all_test_files)

    def afiseaza_performanta_finala(self) -> None:
        """Afiseaza scorurile finale memorate."""
        scores_by_category = getattr(self, "final_scores_by_category", {})
        scores_all = getattr(self, "final_scores_all", None)

        if not scores_by_category and scores_all is None:
            self.logger.console_step("performanta finala: nu exista teste rulabile")
            return

        self.logger.console_step("performanta finala:")

        for category in sorted(scores_by_category):
            self.logger.console_step(
                self._format_final_score_line(category, scores_by_category[category])
            )

        if scores_all is not None:
            self.logger.console_step(self._format_final_score_line("total", scores_all))

    def arhiveaza(self) -> None:
        """
        Arhiveaza artefactele sesiunii curente, daca exista.
        """
        self.logger.console_step("arhivez rezultatele")

        if not self.archive_manager.has_any_artifacts_to_archive():
            self.logger.debug("Nu exista artefacte de arhivat.")
            return

        result = self.archive_manager.archive_current_session_artifacts()
        self.logger.debug(
            self.archive_manager.format_archive_result_for_debug(result)
        )

    def afiseaza_reguli_adaugate(self) -> None:
        """
        Afiseaza rezultatul final al sesiunii curente.
        """
        self.logger.console_step("Rezultate finale:")
        self.afiseaza_rezumat_generare()
        self.afiseaza_performanta_finala()
        self.logger.print_last_added_rules(self.numar_reguli_adaugate)
