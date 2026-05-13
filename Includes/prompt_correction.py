from __future__ import annotations
from pathlib import Path


class PromptCorrectionMixin:
    def build_correction_prompt(
        self,
        testing_md_path: Path,
        validation_error: str,
        proposed_function: str | None = None,
        bullet_index: int | None = None,
    ) -> str:
        """
        Construieste promptul pentru corectarea unei propuneri invalide de test.

        Logica:
        - in etapa pe subtipuri existente, corectarea ramane legata de subtipul cerut;
        - in etapa de descoperire, corectarea ramane in aceeasi categorie si aceeasi
          zona generala de testare, dar poate ajusta ideea concreta pentru validitate;
        - formularea este afirmativa, scurta si orientata spre test pytest valid.
        """
        if not validation_error:
            raise ValueError(
                "validation_error este necesara pentru construirea promptului de corectie."
            )

        common = self._get_common_category_context(testing_md_path)
        format_instructions = self.build_format_instructions()
        proposed_function = proposed_function or "# Empty or unusable previous answer"

        if bullet_index is not None:
            rules_initial_tests, _, _ = self._get_rules_sections()
            bullets = self.workspace.extract_testing_rule_bullets(testing_md_path)

            if bullet_index < 0 or bullet_index >= len(bullets):
                raise ValueError(
                    "bullet_index este invalid pentru construirea promptului de corectie pe subtip."
                )

            explicit_rule_text = bullets[bullet_index]

            correction_instructions = (
                f"{format_instructions}"
                "Repair the proposed test so it becomes one valid pytest test.\n"
                "Keep the requested test instruction as the testing purpose.\n"
                "Use the validation error to fix the concrete problem.\n"
                "Use behavior reachable through normal calls to the provided source code.\n"
                "Return one complete test function.\n"
            ).strip()

            prompt_parts = [
                rules_initial_tests,
                correction_instructions,
                (
                    f"Category: {common['category']}\n"
                    "Correction context: existing subtype tests stage.\n"
                    f"Requested instruction number: {bullet_index + 1}\n"
                    f"Requested test instruction: {explicit_rule_text}"
                ),
                (
                    "Source code to test:\n"
                    f"```python\n{common['source_code']}\n```"
                ),
                (
                    "Previous proposed answer:\n"
                    f"```python\n{proposed_function}\n```"
                ),
                f"Validation error:\n{validation_error}",
            ]

            return "\n\n".join(part.strip() for part in prompt_parts if part.strip())

        _, rules_new_tests, _ = self._get_rules_sections()
        next_bullet_number = int(common["explicit_bullets_count"]) + 1

        existing_rules_section = self._build_existing_explicit_rules_section(
            explicit_bullets=(
                common["explicit_bullets"]
                if isinstance(common["explicit_bullets"], list)
                else []
            )
        )

        correction_instructions = (
            f"{format_instructions}"
            "Repair the proposed test so it becomes one valid pytest test.\n"
            "Keep the requested category and the same general testing area.\n"
            "Use the validation error to fix the concrete problem.\n"
            "Adjust concrete inputs, expected result, or assertion when needed.\n"
            "Use behavior reachable through normal calls to the provided source code.\n"
            "Keep the corrected test distinct from accepted numbered rules and rejected attempts.\n"
            "Return one complete test function.\n"
        ).strip()

        prompt_parts = [
            rules_new_tests,
            common["general_category_rules"],
            correction_instructions,
            (
                f"Category: {common['category']}\n"
                "Correction context: new tests stage.\n"
                f"Existing explicit subtypes in this category: {common['explicit_bullets_count']}\n"
                f"Next subtype number if a reusable subtype is accepted: {next_bullet_number}"
            ),
            existing_rules_section,
            (
                "Current accepted tests for this category:\n"
                f"```python\n{common['current_category_tests']}\n```"
            ),
            (
                "Source code to test:\n"
                f"```python\n{common['source_code']}\n```"
            ),
            (
                "Previous proposed answer:\n"
                f"```python\n{proposed_function}\n```"
            ),
            f"Validation error:\n{validation_error}",
        ]

        return "\n\n".join(part.strip() for part in prompt_parts if part.strip())
