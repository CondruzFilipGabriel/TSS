from __future__ import annotations

from Includes.Config import AppConfig
from Includes.Logger import Logger
from Includes.WorkspaceManager import WorkspaceManager
from Includes.prompt_common import PromptCommonMixin
from Includes.prompt_stages import PromptStagesMixin
from Includes.prompt_correction import PromptCorrectionMixin


class PromptBuilder(
    PromptCommonMixin,
    PromptStagesMixin,
    PromptCorrectionMixin,
):
    """Construieste prompturile trimise catre Ollama."""

    def __init__(
        self,
        config: AppConfig,
        workspace: WorkspaceManager,
        logger: Logger,
    ) -> None:
        self.config = config
        self.workspace = workspace
        self.logger = logger


    def build_prompt(
        self,
        state: int,
        testing_md_path: Path,
        bullet_index: int | None = None,
        proposed_function: str | None = None,
        validation_error: str | None = None,
        accepted_function: str | None = None,
        failed_attempts: list[tuple[str, str]] | None = None,
        attempt_number: int | None = None,
        attempts_without_progress: int | None = None,
        max_attempts_without_progress: int = 3,
        performance_summary: str | None = None,
        previous_rule_response: str | None = None,
        reformulation_feedback: str | None = None,
        refinement_mode: bool = False,
    ) -> str:
        """
        Construieste promptul potrivit in functie de starea curenta a fluxului.
        """
        states = self.config.states

        if state == states.TESTE_INITIALE:
            if bullet_index is None:
                raise ValueError("bullet_index este necesar in starea TESTE_INITIALE.")
            return self.build_initial_tests_prompt(
                testing_md_path=testing_md_path,
                bullet_index=bullet_index,
                failed_attempts=failed_attempts,
                attempt_number=attempt_number,
                attempts_without_progress=attempts_without_progress,
                max_attempts_without_progress=max_attempts_without_progress,
                performance_summary=performance_summary,
            )

        if state == states.TESTE_NOI:
            return self.build_new_tests_prompt(
                testing_md_path=testing_md_path,
                failed_attempts=failed_attempts,
                attempt_number=attempt_number,
                attempts_without_progress=attempts_without_progress,
                max_attempts_without_progress=max_attempts_without_progress,
                performance_summary=performance_summary,
            )

        if state == states.CORECTEAZA_PROPUNERE:
            if not validation_error:
                raise ValueError(
                    "validation_error este necesara in starea CORECTEAZA_PROPUNERE."
                )

            return self.build_correction_prompt(
                testing_md_path=testing_md_path,
                validation_error=validation_error,
                proposed_function=proposed_function,
                bullet_index=bullet_index,
            )

        if state == states.RULE_SI_REASONING:
            if not accepted_function:
                raise ValueError(
                    "accepted_function este necesara in starea RULE_SI_REASONING."
                )

            return self.build_rule_and_reasoning_prompt(
                testing_md_path=testing_md_path,
                accepted_function=accepted_function,
                previous_rule_response=previous_rule_response,
                reformulation_feedback=reformulation_feedback,
                refinement_mode=refinement_mode,
            )

        raise ValueError("Stare necunoscuta pentru construirea promptului.")


    def build_prompt_preview(
        self,
        state: int,
        testing_md_path: Path,
        bullet_index: int | None = None,
        proposed_function: str | None = None,
        validation_error: str | None = None,
        accepted_function: str | None = None,
        failed_attempts: list[tuple[str, str]] | None = None,
        attempt_number: int | None = None,
        attempts_without_progress: int | None = None,
        max_attempts_without_progress: int = 3,
        performance_summary: str | None = None,
        previous_rule_response: str | None = None,
        reformulation_feedback: str | None = None,
        refinement_mode: bool = False,
        preview_length: int = 300,
    ) -> str:
        """
        Construieste promptul complet si returneaza doar un preview scurt.
        """
        full_prompt = self.build_prompt(
            state=state,
            testing_md_path=testing_md_path,
            bullet_index=bullet_index,
            proposed_function=proposed_function,
            validation_error=validation_error,
            accepted_function=accepted_function,
            failed_attempts=failed_attempts,
            attempt_number=attempt_number,
            attempts_without_progress=attempts_without_progress,
            max_attempts_without_progress=max_attempts_without_progress,
            performance_summary=performance_summary,
            previous_rule_response=previous_rule_response,
            reformulation_feedback=reformulation_feedback,
            refinement_mode=refinement_mode,
        )

        compact_prompt = full_prompt.replace("\n", " ").strip()
        if len(compact_prompt) <= preview_length:
            return compact_prompt

        return compact_prompt[:preview_length] + "..."
