from __future__ import annotations
from pathlib import Path


class AutoRuleGenerationMixin:
    def obtine_rule_si_reasoning_valid(
        self,
        testing_md_path: Path,
        accepted_function: str,
        previous_rule_response: str | None = None,
        reformulation_feedback: str | None = None,
        refinement_mode: bool = False,
        max_attempts: int | None = None,
    ) -> tuple[str | None, str | None, str | None]:
        """
        Obtine o pereche Rule / Reasoning valida formal.

        Returneaza:
        - raw_rule_response
        - rule
        - reasoning

        Daca nu reuseste sa obtina o varianta valida in bugetul de incercari,
        returneaza (None, None, None).
        """
        self.state = self.config.states.RULE_SI_REASONING

        if max_attempts is None:
            max_attempts = self.config.timeouts.max_corectie_attempts + 1

        previous_response_local = previous_rule_response or ""
        feedback_local = reformulation_feedback or ""

        for attempt_index in range(1, max_attempts + 1):
            prompt = self.prompt_builder.build_prompt(
                state=self.state,
                testing_md_path=testing_md_path,
                accepted_function=accepted_function,
                previous_rule_response=previous_response_local or None,
                reformulation_feedback=feedback_local or None,
                refinement_mode=refinement_mode,
            )

            ollama_response = self.ollama_client.generate(prompt)
            raw_rule_response = (ollama_response.text or "").strip()

            parsed_response = self.response_parser.parse_response(raw_rule_response)
            rule, reasoning = self.response_parser.extract_rule_and_reasoning_from_comments(
                parsed_response.metadata_comments or raw_rule_response
            )

            validation_message = self.validate_rule_and_reasoning_candidate(
                raw_response=raw_rule_response,
                rule=rule,
                reasoning=reasoning,
                testing_md_path=testing_md_path,
                accepted_function=accepted_function,
            )

            if validation_message == "Valid":
                return raw_rule_response, rule, (reasoning or "").strip()

            self.logger.debug(
                "Rule/Reasoning necesita reformulare. "
                f"Motiv: {validation_message}"
            )

            if attempt_index >= max_attempts:
                break

            previous_response_local = raw_rule_response
            feedback_local = validation_message
            self.ollama_client.reset_context()

        return None, None, None

    def solicita_rule_si_reasoning(
        self,
        testing_md_path: Path,
        accepted_function: str,
    ) -> tuple[str | None, str]:
        """
        Cere separat metadatele Rule / Reasoning pentru un test deja acceptat.

        Daca modelul nu poate formula o regula valida, se returneaza:
        - rule = None
        - reasoning = motiv tehnic scurt

        In acest caz testul ramane acceptat, dar nu se adauga regula in testing_*.md.
        """
        fallback_reasoning = (
            "The accepted test improved the category, but no valid reusable rule was generated."
        )

        first_raw, first_rule, first_reasoning = self.obtine_rule_si_reasoning_valid(
            testing_md_path=testing_md_path,
            accepted_function=accepted_function,
            refinement_mode=False,
        )

        if not first_rule or not first_reasoning:
            return None, fallback_reasoning

        first_rule = self.normalize_rule_text(
            rule=first_rule,
            fallback_rule="",
        )

        if not first_rule or self.is_weak_generic_rule(first_rule):
            return None, fallback_reasoning

        self.ollama_client.reset_context()

        refinement_feedback = (
            "Improve the previous Rule and Reasoning.\n"
            "Keep the same testing idea.\n"
            "Use the category vocabulary.\n"
            "Make the rule clearer and reusable for similar functions.\n"
            "Return exactly the two requested comment lines."
        )

        refined_raw, refined_rule, refined_reasoning = self.obtine_rule_si_reasoning_valid(
            testing_md_path=testing_md_path,
            accepted_function=accepted_function,
            previous_rule_response=first_raw,
            reformulation_feedback=refinement_feedback,
            refinement_mode=True,
            max_attempts=2,
        )

        if not refined_rule or not refined_reasoning:
            return first_rule, first_reasoning

        refined_rule = self.normalize_rule_text(
            rule=refined_rule,
            fallback_rule="",
        )

        if not refined_rule or self.is_weak_generic_rule(refined_rule):
            return first_rule, first_reasoning

        best_rule, best_reasoning = self.choose_better_rule_candidate(
            testing_md_path=testing_md_path,
            first_rule=first_rule,
            first_reasoning=first_reasoning,
            refined_rule=refined_rule,
            refined_reasoning=refined_reasoning,
        )

        if not best_rule or self.is_weak_generic_rule(best_rule):
            return None, fallback_reasoning

        return best_rule, best_reasoning

    def salveaza_regula_acceptata_daca_exista(
        self,
        category: str,
        testing_md_path: Path,
        rule: str | None,
        reasoning: str,
        improvement: str,
    ) -> bool:
        """
        Salveaza regula acceptata in Logs.jsonl si testing_*.md doar daca regula
        este valida si negenerica.

        Returneaza True daca regula a fost salvata, altfel False.
        """
        cleaned_rule = (rule or "").strip()

        if not cleaned_rule or self.is_weak_generic_rule(cleaned_rule):
            self.logger.warning(
                f"Testul a fost acceptat in categoria {category}, dar regula nu a putut fi formulata valid. "
                "Testul ramane in fisierul categoriei, insa nu se adauga regula in testing_*.md."
            )
            self.logger.debug(
                f"Motiv Rule/Reasoning nesalvat pentru {category}: {reasoning}"
            )
            return False

        self.logger.append_rule(
            category=category,
            rule=cleaned_rule,
            reasoning=reasoning,
            improvement=improvement,
        )

        self.workspace.append_rule_bullet_to_testing_md(
            testing_md_path=testing_md_path,
            rule_text=cleaned_rule,
        )

        return True
