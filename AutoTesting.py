from __future__ import annotations

from pathlib import Path

from Includes.Archive import ArchiveManager
from Includes.Cleanup import CleanupManager
from Includes.Config import AppConfig
from Includes.Logger import Logger
from Includes.OllamaClient import OllamaClient
from Includes.PromptBuilder import PromptBuilder
from Includes.ResponseParser import ResponseParser
from Includes.TestValidator import TestValidator
from Includes.TestsPerformance import PerformanceScores, TestsPerformance
from Includes.WorkspaceManager import WorkspaceManager
from Includes.auto_goal import AutoGoalMixin
from Includes.auto_initial_stage import AutoInitialStageMixin
from Includes.auto_new_stage import AutoNewStageMixin
from Includes.auto_proposals import AutoProposalMixin
from Includes.auto_reporting import AutoReportingMixin
from Includes.auto_request import AutoRequestMixin
from Includes.auto_rule_generation import AutoRuleGenerationMixin
from Includes.auto_rule_utils import AutoRuleUtilsMixin


class AutoTesting(
    AutoGoalMixin,
    AutoRequestMixin,
    AutoInitialStageMixin,
    AutoNewStageMixin,
    AutoRuleUtilsMixin,
    AutoRuleGenerationMixin,
    AutoProposalMixin,
    AutoReportingMixin,
):
    """
    Orchestratorul principal al framework-ului.

    Root-ul ramane responsabil doar pentru conectarea componentelor si pentru
    fluxul general. Logica detaliata este mutata in modulele din Includes/.
    """

    def __init__(
        self,
        debugging_enabled: bool = False,
        print_debug: bool = True,
    ) -> None:
        self.config = AppConfig(Path(__file__).resolve())

        self.logger = Logger(
            config=self.config,
            debugging_enabled=debugging_enabled,
            print_debug=print_debug,
        )
        self.workspace = WorkspaceManager(
            config=self.config,
            logger=self.logger,
        )
        self.cleanup_manager = CleanupManager(
            config=self.config,
            logger=self.logger,
            workspace=self.workspace,
        )
        self.response_parser = ResponseParser()
        self.prompt_builder = PromptBuilder(
            config=self.config,
            workspace=self.workspace,
            logger=self.logger,
        )
        self.ollama_client = OllamaClient(
            config=self.config,
            logger=self.logger,
        )
        self.validator = TestValidator(
            config=self.config,
            logger=self.logger,
            workspace=self.workspace,
            response_parser=self.response_parser,
        )
        self.tests_performance = TestsPerformance(
            config=self.config,
            logger=self.logger,
            workspace=self.workspace,
        )
        self.archive_manager = ArchiveManager(
            config=self.config,
            logger=self.logger,
            workspace=self.workspace,
        )

        self.state: int = self.config.states.TESTE_INITIALE
        self.numar_reguli_adaugate: int = 0
        self.fisiere_testing_md: list[Path] = []
        self.fisiere_testing: dict[str, str] = {}
        self.failed_attempts_by_category: dict[str, list[tuple[str, str]]] = {}
        self.rejected_hashes_by_category: dict[str, set[str]] = {}
        self.generated_tests_by_category: dict[str, int] = {}
        self.accepted_tests_by_category: dict[str, int] = {}
        self.final_scores_by_category: dict[str, PerformanceScores] = {}
        self.final_scores_all: PerformanceScores | None = None

    def verifica_conditii_initiale(self) -> None:
        """Valideaza structura minima si pregateste fisierele de lucru."""
        self.logger.console_step("verific existenta conditiilor de rulare")
        self.workspace.validate_initial_project_structure()

        self.fisiere_testing_md = self.workspace.get_testing_md_files()
        self.fisiere_testing = self.workspace.build_testing_file_mapping()

        self.logger.debug(
            f"Conditiile initiale sunt valide. Model Ollama: {self.config.ollama.model}"
        )

    def get_current_scores(
        self,
        selected_test_files: list[str] | None = None,
    ) -> PerformanceScores:
        """Returneaza scorurile curente pentru fisierele selectate."""
        return self.tests_performance.get_current_scores(selected_test_files)

    def format_scores_for_debug(self, scores: PerformanceScores) -> str:
        """Formateaza scorurile pentru mesajele de debug."""
        return self.tests_performance.format_scores_for_debug(scores)

    def run(self) -> None:
        """Ruleaza fluxul complet al framework-ului."""
        self.logger.section("Pregatiri initiale:")
        self.cleanup_manager.cleanup_before_run()
        self.verifica_conditii_initiale()
        self.logger.separator()

        self.scrie_teste_initiale()
        self.logger.separator()

        if self.are_all_categories_complete():
            self.logger.debug(
                "Etapa de generare a testelor noi este sarita deoarece toate categoriile sunt complete."
            )
        else:
            self.gaseste_teste_noi()
        self.logger.separator()

        self.colecteaza_performanta_finala()
        self.logger.separator()

        self.logger.section("Final:")
        self.arhiveaza()
        self.cleanup_manager.cleanup_after_run()
        self.afiseaza_reguli_adaugate()


def main() -> None:
    """Punct minim de intrare pentru executie."""
    try:
        auto_testing = AutoTesting(
            debugging_enabled=True,
            print_debug=True,
        )
        auto_testing.run()
    except (FileNotFoundError, ValueError, RuntimeError, OSError, Exception) as error:
        print(error)


if __name__ == "__main__":
    main()
