from __future__ import annotations
from pathlib import Path


class PromptCommonMixin:
    def build_format_instructions(self) -> str:
        """
        Construieste instructiunile comune de format pentru generarea functiei de test.

        Formularea este afirmativa si compacta, pentru a ajuta modelul local sa
        produca direct forma asteptata.
        """
        return (
            "Return exactly one complete concrete Python pytest test function.\n"
            "The response contains only the function definition and its body.\n"
            "The function name starts with test_.\n"
            "Use a unique function name that is not already present in the accepted tests.\n"
            "The framework provides imports when needed.\n"
            "Use direct assertions or pytest.raises inside the function.\n"
            "Do not include markdown fences, explanations, imports, helper functions, or placeholder code.\n"
        )

    def _get_rules_sections(self) -> tuple[str, str, str]:
        """
        Extrage cele trei sectiuni principale din Rules.md.

        Returneaza:
        - rules_initial_tests
        - rules_new_tests
        - rules_rule_and_reasoning
        """
        rules_file_path = self.workspace.get_rules_file_path()

        rules_initial_tests = self.workspace.extract_section_after_header(
            markdown_path=rules_file_path,
            header_index=0,
            until_next_header=True,
        )

        rules_new_tests = self.workspace.extract_section_after_header(
            markdown_path=rules_file_path,
            header_index=1,
            until_next_header=True,
        )

        rules_rule_and_reasoning = self.workspace.extract_section_after_header(
            markdown_path=rules_file_path,
            header_index=2,
            until_next_header=False,
        )

        return (
            rules_initial_tests,
            rules_new_tests,
            rules_rule_and_reasoning,
        )

    def _get_common_category_context(
        self,
        testing_md_path: Path,
    ) -> dict[str, str | int | list[str]]:
        """
        Construieste contextul comun unei categorii de testare.

        Include:
        - numele categoriei
        - regulile generale ale categoriei
        - codul sursa din to_test.py
        - continutul curent al fisierului de test asociat
        - numarul de bullet-uri explicite existente
        - lista bullet-urilor explicite existente
        """
        category = self.workspace.get_category_name_from_testing_md(testing_md_path)
        general_category_rules = self.workspace.extract_general_category_rules(
            testing_md_path
        )
        source_code = self.workspace.read_file_under_test_source()
        current_category_tests = self.workspace.read_category_test_file_content(
            testing_md_path
        )
        explicit_bullets = self.workspace.extract_testing_rule_bullets(
            testing_md_path
        )
        explicit_bullets_count = len(explicit_bullets)

        return {
            "category": category,
            "general_category_rules": general_category_rules,
            "source_code": source_code,
            "current_category_tests": current_category_tests,
            "explicit_bullets_count": explicit_bullets_count,
            "explicit_bullets": explicit_bullets,
        }

    def _build_existing_explicit_rules_section(
        self,
        explicit_bullets: list[str] | None,
    ) -> str:
        """
        Construieste o sectiune separata cu subtipurile explicite deja existente
        in fisierul categoriei.
        """
        if not explicit_bullets:
            return "Existing explicit subtypes in this category:\n(none)"

        lines = ["Existing explicit subtypes in this category:"]
        for index, bullet in enumerate(explicit_bullets, start=1):
            lines.append(f"{index}. {bullet}")

        return "\n".join(lines).strip()

    def _build_rejected_attempts_section(
        self,
        failed_attempts: list[tuple[str, str]] | None = None,
        max_items: int = 5,
    ) -> str:
        """
        Construieste o sectiune scurta cu incercarile respinse anterior.

        Parametru:
        - failed_attempts: lista de tuple de forma
        (proposed_function, rejection_reason)

        Scop:
        - pentru etapa 2, modelul trebuie sa vada ce s-a incercat deja si de ce
        a fost respins, ca sa evite repetarea acelorasi idei.
        """
        if not failed_attempts:
            return ""

        configured_max_items = getattr(
            getattr(self.config, "generation_limits", None),
            "max_failed_attempts_kept_per_scope",
            max_items,
        )
        trimmed_attempts = failed_attempts[-configured_max_items:]
        blocks: list[str] = [
            "Previously tried and rejected attempts in this category:",
            "Use them as negative examples.",
            "Do not repeat the same test idea, the same path, or a superficial variation of a rejected attempt.",
        ]

        for index, (proposed_function, rejection_reason) in enumerate(
            trimmed_attempts,
            start=1,
        ):
            clean_function = (proposed_function or "").strip()
            clean_reason = (rejection_reason or "").strip()

            if not clean_function:
                clean_function = "# Empty or unusable previous answer"

            if not clean_reason:
                clean_reason = "Rejected without an explicit recorded reason."

            blocks.append(
                (
                    f"Rejected attempt {index}:\n"
                    f"```python\n{clean_function}\n```\n"
                    f"Rejection reason:\n{clean_reason}"
                )
            )

        return "\n\n".join(blocks).strip()
