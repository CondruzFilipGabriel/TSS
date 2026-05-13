from __future__ import annotations
import hashlib
import re
from pathlib import Path
from Includes.performance_models import PerformanceScores


class AutoRequestMixin:
    def _build_ollama_summary(
        self,
        testing_md_path: Path,
        bullet_index: int | None,
        attempt_number: int | None,
        correction: bool = False,
    ) -> str:
        """Construieste mesajul scurt afisat in terminal pentru apelul Ollama."""
        category = self.workspace.get_category_name_from_testing_md(testing_md_path)

        if correction:
            return f"{category} / corectie raspuns invalid"

        if bullet_index is None:
            return f"{category} / descoperire test nou"

        bullets = self.workspace.extract_testing_rule_bullets(testing_md_path)
        instruction = "subtip necunoscut"
        if 0 <= bullet_index < len(bullets):
            instruction = bullets[bullet_index]

        return f"{category} / subtip {bullet_index + 1}: {instruction}"

    def solicita_functie_valida(
        self,
        testing_md_path: Path,
        bullet_index: int | None = None,
        remaining_ai_budget_sec: float | None = None,
        failed_attempts: list[tuple[str, str]] | None = None,
        attempt_number: int | None = None,
        attempts_without_progress: int | None = None,
        max_attempts_without_progress: int | None = None,
        performance_summary: str | None = None,
    ) -> tuple[str | None, float]:
        """
        Solicita modelului o functie valida si, daca este necesar, cere
        corectarea ei de mai multe ori.

        Returneaza:
        - function_code valid sau None
        - timpul total consumat de AI pentru aceasta secventa de generare

        Noua logica:
        - in etapa initiala, bullet_index identifica subtipul explicit cerut
          din testing_*.md;
        - acelasi subtip poate fi folosit in mai multe incercari succesive;
        - promptul poate primi scorurile curente, numarul incercarii si
          incercarile respinse anterior pentru acel subtip;
        - in etapa de descoperire, bullet_index ramane None si fluxul vechi
          continua sa caute idei noi in categorie.
        """
        current_function_code = ""
        current_validation_error = ""
        ai_time_spent = 0.0
        empty_answers_count = 0
        category = self.workspace.get_category_name_from_testing_md(testing_md_path)
        is_new_tests_stage = bullet_index is None

        if bullet_index is not None:
            self.state = self.config.states.TESTE_INITIALE
            if max_attempts_without_progress is None:
                max_attempts_without_progress = (
                    self.config.generation_limits.max_existing_subtype_attempts_without_progress
                )
        else:
            self.state = self.config.states.TESTE_NOI
            if max_attempts_without_progress is None:
                max_attempts_without_progress = (
                    self.config.generation_limits.max_discovery_attempts_without_progress
                )

        prompt = self.prompt_builder.build_prompt(
            state=self.state,
            testing_md_path=testing_md_path,
            bullet_index=bullet_index,
            failed_attempts=failed_attempts,
            attempt_number=attempt_number,
            attempts_without_progress=attempts_without_progress,
            max_attempts_without_progress=max_attempts_without_progress,
            performance_summary=performance_summary,
        )

        max_total_attempts = self.config.timeouts.max_corectie_attempts + 1

        for attempt_index in range(1, max_total_attempts + 1):
            if (
                remaining_ai_budget_sec is not None
                and ai_time_spent >= remaining_ai_budget_sec
            ):
                self.logger.ai_technical(
                    "limita de timp a expirat inainte de obtinerea unei functii valide."
                )
                return None, ai_time_spent

            summary = self._build_ollama_summary(
                testing_md_path=testing_md_path,
                bullet_index=bullet_index,
                attempt_number=attempt_number,
                correction=(self.state == self.config.states.CORECTEAZA_PROPUNERE),
            )
            self.logger.debug(f"Cerere Ollama: {summary}")
            ollama_response = self.ollama_client.generate(prompt)
            ai_time_spent += ollama_response.duration_sec

            validation_result = self.validator.validate_response_text(
                ollama_response.text
            )
            parsed_response = validation_result.parsed_response
            current_function_code = parsed_response.function_code

            if validation_result.is_valid:
                return current_function_code, ai_time_spent

            if not (ollama_response.text or "").strip():
                empty_answers_count += 1
            elif not current_function_code.strip():
                empty_answers_count += 1
            else:
                empty_answers_count = 0

            self.logger.debug(
                f"Validare esuata pentru categoria {category}: {validation_result.message}"
            )

            function_or_answer_to_remember = (
                current_function_code.strip()
                or parsed_response.cleaned_text.strip()
                or (ollama_response.text or "").strip()
                or "# Empty or unusable previous answer"
            )

            if failed_attempts is not None:
                candidate = (
                    function_or_answer_to_remember,
                    validation_result.message,
                )
                if candidate not in failed_attempts:
                    failed_attempts.append(candidate)
                    if len(failed_attempts) > self.config.generation_limits.max_failed_attempts_kept_per_scope:
                        del failed_attempts[:-self.config.generation_limits.max_failed_attempts_kept_per_scope]

            if is_new_tests_stage:
                self.remember_failed_attempt(
                    category=category,
                    function_code=function_or_answer_to_remember,
                    rejection_reason=validation_result.message,
                )

            if (
                empty_answers_count
                > self.config.timeouts.max_empty_answers_consecutive
            ):
                self.logger.ai_technical(
                    "prea multe raspunsuri goale sau inutilizabile de la Ollama."
                )
                return None, ai_time_spent

            if self.validator.is_timeout_error(validation_result.message):
                self.logger.ai_technical(
                    "a aparut un timeout la validare. Propunerea este respinsa."
                )
                return None, ai_time_spent

            if attempt_index >= max_total_attempts:
                self.logger.ai_technical(
                    "a fost atins numarul maxim de tentative de corectie."
                )
                return None, ai_time_spent

            self.logger.ai_technical("validez functia propusa si cer o corectie...")
            self.state = self.config.states.CORECTEAZA_PROPUNERE
            current_validation_error = validation_result.message

            prompt = self.prompt_builder.build_prompt(
                state=self.state,
                testing_md_path=testing_md_path,
                bullet_index=bullet_index,
                proposed_function=(
                    current_function_code
                    or parsed_response.cleaned_text
                    or (ollama_response.text or "")
                ),
                validation_error=current_validation_error,
            )

            self.ollama_client.reset_context()

        return None, ai_time_spent
