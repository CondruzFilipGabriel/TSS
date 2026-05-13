from __future__ import annotations
from pathlib import Path


class PromptStagesMixin:
    def build_initial_tests_prompt(
        self,
        testing_md_path: Path,
        bullet_index: int,
        failed_attempts: list[tuple[str, str]] | None = None,
        attempt_number: int | None = None,
        attempts_without_progress: int | None = None,
        max_attempts_without_progress: int = 3,
        performance_summary: str | None = None,
    ) -> str:
        """
        Construieste promptul pentru etapa initiala pe subtipuri existente.

        Noua logica:
        - bullet_index selecteaza subtipul explicit din testing_*.md;
        - modelul poate genera mai multe teste pentru acelasi subtip;
        - promptul include testele deja acceptate si ultimele incercari respinse,
          pentru a reduce repetitiile;
        - criteriul de acceptare ramane in orchestrator: testul trebuie sa fie valid
          si sa imbunatateasca scorul categoriei.
        """
        rules_initial_tests, _, _ = self._get_rules_sections()
        common = self._get_common_category_context(testing_md_path)
        bullets = self.workspace.extract_testing_rule_bullets(testing_md_path)

        if bullet_index < 0 or bullet_index >= len(bullets):
            raise ValueError("bullet_index este invalid pentru etapa pe subtipuri existente.")

        explicit_subtype_text = bullets[bullet_index]
        format_instructions = self.build_format_instructions()
        rejected_attempts_section = self._build_rejected_attempts_section(
            failed_attempts=failed_attempts
        )

        stage_context_lines = [
            f"Category: {common['category']}",
            "Stage: existing subtype tests",
            f"Requested instruction number: {bullet_index + 1}",
            f"Requested test instruction: {explicit_subtype_text}",
            "Write one pytest test for this instruction only.",
            "Use one concrete case.",
            "Use a unique test function name.",
        ]

        if attempt_number is not None:
            stage_context_lines.append(f"Attempt number for this subtype: {attempt_number}")

        if attempts_without_progress is not None:
            stage_context_lines.append(
                f"Current consecutive attempts without progress for this subtype: {attempts_without_progress}"
            )
            stage_context_lines.append(
                f"Stop threshold handled by the framework: {max_attempts_without_progress} attempts without progress"
            )

        prompt_parts: list[str] = [
            rules_initial_tests,
            (
                f"{format_instructions}"
                "Important for this request:\n"
                "- Follow the requested test instruction exactly.\n"
                "- Do not invent a different testing goal in this stage.\n"
                "- Do not repeat an already accepted test.\n"
                "- Do not repeat a previously rejected attempt.\n"
                "- Prefer a simple test with an exact assertion.\n"
            ).strip(),
            "\n".join(stage_context_lines),
            (
                "Current accepted tests for this category:\n"
                f"```python\n{common['current_category_tests']}\n```"
            ),
        ]

        if performance_summary:
            prompt_parts.append(
                "Current measured performance for this category:\n"
                f"```text\n{performance_summary.strip()}\n```"
            )

        if rejected_attempts_section:
            prompt_parts.append(rejected_attempts_section)

        prompt_parts.append(
            "Source code to test:\n"
            f"```python\n{common['source_code']}\n```"
        )

        return "\n\n".join(part.strip() for part in prompt_parts if part.strip())

    def build_new_tests_prompt(
        self,
        testing_md_path: Path,
        failed_attempts: list[tuple[str, str]] | None = None,
        attempt_number: int | None = None,
        attempts_without_progress: int | None = None,
        max_attempts_without_progress: int = 3,
        performance_summary: str | None = None,
    ) -> str:
        """
        Construieste promptul pentru descoperirea de teste noi dupa epuizarea
        subtipurilor predefinite din fisierul categoriei.

        In aceasta etapa modelul primeste descrierea categoriei si subtipurile
        deja existente, deoarece scopul este sa caute o idee noua, diferita de
        ce a fost deja incercat in categoria respectiva.
        """
        _, rules_new_tests, _ = self._get_rules_sections()
        common = self._get_common_category_context(testing_md_path)
        format_instructions = self.build_format_instructions()

        existing_rules_section = self._build_existing_explicit_rules_section(
            explicit_bullets=(
                common["explicit_bullets"]
                if isinstance(common["explicit_bullets"], list)
                else []
            )
        )
        rejected_attempts_section = self._build_rejected_attempts_section(
            failed_attempts=failed_attempts
        )

        next_bullet_number = int(common["explicit_bullets_count"]) + 1

        stage_context_lines = [
            f"Category: {common['category']}",
            "Stage: new subtype discovery after predefined subtypes were tried",
            f"Existing explicit subtypes in this category: {common['explicit_bullets_count']}",
            f"Next subtype number if a reusable subtype is later accepted: {next_bullet_number}",
        ]

        if attempt_number is not None:
            stage_context_lines.append(
                f"Discovery attempt number for this category: {attempt_number}"
            )

        if attempts_without_progress is not None:
            stage_context_lines.append(
                f"Current consecutive discovery attempts without progress: {attempts_without_progress}"
            )
            stage_context_lines.append(
                f"Stop threshold handled by the framework: {max_attempts_without_progress} attempts without progress"
            )

        prompt_parts: list[str] = [
            rules_new_tests,
            (
                "Category instruction:\n"
                f"{common['general_category_rules']}\n\n"
                "Use this category instruction as a requirement, not as background text.\n"
                "The new test must belong to this category.\n"
            ).strip(),
            (
                f"{format_instructions}"
                "Important for this request:\n"
                "- Create one new test idea for this category.\n"
                "- The idea must be different from the explicit subtypes listed below.\n"
                "- Do not repeat a previously rejected idea.\n"
                "- Do not make only a cosmetic variation of an accepted or rejected test.\n"
                "- For functional: prefer a new visible behavior, output class, input class, boundary, exception, or final returned value.\n"
                "- For structural: prefer a new branch outcome, compound-condition outcome, loop count, guard path, assignment path, or return path.\n"
                "- Prefer a test that can improve branch coverage or mutation score for this category.\n"
            ).strip(),
            "\n".join(stage_context_lines),
            existing_rules_section,
            (
                "Current accepted tests for this category:\n"
                f"```python\n{common['current_category_tests']}\n```"
            ),
        ]

        if performance_summary:
            prompt_parts.append(
                "Current measured performance for this category:\n"
                f"```text\n{performance_summary.strip()}\n```"
            )

        if rejected_attempts_section:
            prompt_parts.append(rejected_attempts_section)

        prompt_parts.append(
            "Source code to test:\n"
            f"```python\n{common['source_code']}\n```"
        )

        return "\n\n".join(part.strip() for part in prompt_parts if part.strip())

    def build_rule_and_reasoning_prompt(
        self,
        testing_md_path: Path,
        accepted_function: str,
        previous_rule_response: str | None = None,
        reformulation_feedback: str | None = None,
        refinement_mode: bool = False,
    ) -> str:
        """
        Construieste promptul pentru cererea metadatelor Rule / Reasoning
        dupa ce testul a fost deja acceptat.

        Formularea este scurta si afirmativa:
        - modelul vede categoria, regulile existente si testul acceptat
        - daca exista feedback anterior, il foloseste pentru a produce o varianta valida
        - refinement_mode cere o versiune mai clara, nu una mai restrictiva
        """
        _, _, rules_rule_and_reasoning = self._get_rules_sections()
        common = self._get_common_category_context(testing_md_path)

        if not accepted_function.strip():
            raise ValueError(
                "accepted_function este necesara pentru construirea promptului de regula si motivare."
            )

        existing_rules_section = self._build_existing_explicit_rules_section(
            explicit_bullets=(
                common["explicit_bullets"]
                if isinstance(common["explicit_bullets"], list)
                else []
            )
        )

        prompt_parts: list[str] = [
            rules_rule_and_reasoning,
            common["general_category_rules"],
            f"Category: {common['category']}",
            existing_rules_section,
            (
                "Accepted test function:\n"
                f"```python\n{accepted_function}\n```"
            ),
        ]

        if refinement_mode:
            prompt_parts.append(
                (
                    "Improve the previous Rule and Reasoning.\n"
                    "Keep the same testing idea.\n"
                    "Use the category vocabulary.\n"
                    "Make the rule clearer and reusable for similar functions.\n"
                    "Return exactly the two requested comment lines."
                )
            )

            if previous_rule_response:
                prompt_parts.append(
                    "Previous Rule and Reasoning:\n"
                    f"```text\n{previous_rule_response.strip()}\n```"
                )

            if reformulation_feedback:
                prompt_parts.append(
                    "Feedback to apply:\n"
                    f"{reformulation_feedback.strip()}"
                )

        elif previous_rule_response or reformulation_feedback:
            prompt_parts.append(
                (
                    "Write a corrected Rule and Reasoning.\n"
                    "Use the category vocabulary.\n"
                    "Use semantic terms instead of concrete values or names.\n"
                    "Return exactly the two requested comment lines."
                )
            )

            if previous_rule_response:
                prompt_parts.append(
                    "Previous response:\n"
                    f"```text\n{previous_rule_response.strip()}\n```"
                )

            if reformulation_feedback:
                prompt_parts.append(
                    "Feedback to apply:\n"
                    f"{reformulation_feedback.strip()}"
                )

        return "\n\n".join(part.strip() for part in prompt_parts if part.strip())
