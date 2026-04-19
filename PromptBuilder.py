from __future__ import annotations

"""
PromptBuilder.py

Rol
---
Acest fisier construieste prompturile trimise modelului AI in cadrul
framework-ului de generare automata de teste.

Scopul lui este sa scoata din orchestrator toata logica de compunere a
mesajelor catre model, astfel incat:
- AutoTesting.py sa ramana concentrat pe flux
- regulile de formulare a prompturilor sa fie centralizate
- modificarile de instructiuni sa poata fi facute intr-un singur loc

Ce tipuri de prompturi construieste
-----------------------------------
1. Prompt pentru etapa 1:
   - generarea testelor initiale plecand de la bullet-urile explicite
     din fisierele testing_*.md

2. Prompt pentru etapa 2:
   - generarea unor teste noi, din aceeasi categorie, dincolo de
     bullet-urile deja enumerate

3. Prompt pentru etapa 3:
   - corectarea unei propuneri invalide, pe baza erorii de validare

De ce exista acest modul separat
--------------------------------
In varianta initiala, AutoTesting.py continea metoda
`construieste_prompt_ollama(...)`, care depindea simultan de:
- Rules.md
- fisierele testing_*.md
- to_test.py
- continutul curent al fisierelor test_<categorie>.py
- starea curenta a fluxului

Aceasta logica este suficient de complexa si suficient de distincta
incat merita un fisier separat.

Observatii
----------
1. Acest modul nu trimite prompturile la Ollama. Asta va fi responsabilitatea
   lui OllamaClient.py.

2. Acest modul nu valideaza raspunsurile si nu scrie fisiere.
   El doar compune textul exact care trebuie trimis modelului.

3. Starile folosite aici sunt cele definite in Config.py, pentru a pastra
   compatibilitatea cu fluxul existent din AutoTesting.py.
"""

from pathlib import Path

from Config import AppConfig
from Logger import Logger
from WorkspaceManager import WorkspaceManager


class PromptBuilder:
    """
    Construieste prompturile necesare pentru toate etapele fluxului.

    Parametri:
    - config: configurarea centrala a aplicatiei
    - workspace: managerul de fisiere si continuturi al proiectului
    - logger: logger-ul folosit pentru mesaje de debug
    """

    def __init__(
        self,
        config: AppConfig,
        workspace: WorkspaceManager,
        logger: Logger,
    ) -> None:
        self.config = config
        self.workspace = workspace
        self.logger = logger

    # ------------------------------------------------------------------
    # Instructiuni comune de format
    # ------------------------------------------------------------------

    def build_format_instructions(self) -> str:
        """
        Construieste instructiunile comune de format pentru generarea functiei de test.

        Aceste instructiuni sunt folosite doar pentru:
        - generare teste initiale
        - generare teste noi
        - corectare propunere invalida

        Metadatele Rule / Reasoning se cer separat, dupa acceptarea testului.
        """
        return (
            "Return exactly one complete concrete Python pytest test function and nothing else.\n"
            "Do not write import statements.\n"
            "Do not write markdown.\n"
            "Do not write explanations outside the function.\n"
        )

    # ------------------------------------------------------------------
    # Citirea si compunerea continutului comun
    # ------------------------------------------------------------------

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

    def _get_common_category_context(self, testing_md_path: Path) -> dict[str, str | int]:
        """
        Construieste contextul comun unei categorii de testare.

        Include:
        - numele categoriei
        - regulile generale ale categoriei
        - codul sursa din to_test.py
        - continutul curent al fisierului de test asociat
        - numarul de bullet-uri explicite existente
        """
        category = self.workspace.get_category_name_from_testing_md(testing_md_path)
        general_category_rules = self.workspace.extract_general_category_rules(
            testing_md_path
        )
        source_code = self.workspace.read_file_under_test_source()
        current_category_tests = self.workspace.read_category_test_file_content(
            testing_md_path
        )
        explicit_bullets_count = self.workspace.count_testing_rule_bullets(
            testing_md_path
        )

        return {
            "category": category,
            "general_category_rules": general_category_rules,
            "source_code": source_code,
            "current_category_tests": current_category_tests,
            "explicit_bullets_count": explicit_bullets_count,
        }

    # ------------------------------------------------------------------
    # Prompt etapa 1 - teste initiale
    # ------------------------------------------------------------------

    def build_initial_tests_prompt(
        self,
        testing_md_path: Path,
        bullet_index: int,
    ) -> str:
        """
        Construieste promptul pentru etapa 1: generarea unui test initial
        pe baza unui bullet explicit din fisierul categoriei.
        """
        rules_initial_tests, _, _ = self._get_rules_sections()
        common = self._get_common_category_context(testing_md_path)
        bullets = self.workspace.extract_testing_rule_bullets(testing_md_path)

        if bullet_index < 0 or bullet_index >= len(bullets):
            raise ValueError("bullet_index este invalid pentru etapa de teste initiale.")

        explicit_rule_text = bullets[bullet_index]
        format_instructions = self.build_format_instructions()

        prompt = (
            f"{rules_initial_tests}\n\n"
            f"{common['general_category_rules']}\n\n"
            f"{format_instructions}"
            f"Category: {common['category']}\n"
            f"Explicit rule number: {bullet_index + 1}\n"
            f"Explicit rule text: {explicit_rule_text}\n\n"
            f"Source code to test:\n```python\n{common['source_code']}\n```"
        ).strip()

        return prompt

    # ------------------------------------------------------------------
    # Prompt etapa 2 - teste noi
    # ------------------------------------------------------------------

    def build_new_tests_prompt(
        self,
        testing_md_path: Path,
        failed_attempts: list[tuple[str, str]] | None = None,
    ) -> str:
        """
        Construieste promptul pentru etapa 2: generarea unui test nou,
        dincolo de bullet-urile explicite existente in fisierul categoriei.

        Noua logica:
        - modelul vede testele deja acceptate in categorie
        - modelul vede si incercarile deja respinse, ca sa nu le repete
        - promptul cere explicit o regula cu adevarat noua, nu doar o variatie
        superficiala a unei idei deja esuate
        """
        _, rules_new_tests, _ = self._get_rules_sections()
        common = self._get_common_category_context(testing_md_path)
        format_instructions = self.build_format_instructions()
        rejected_attempts_section = self._build_rejected_attempts_section(
            failed_attempts=failed_attempts
        )

        next_bullet_number = int(common["explicit_bullets_count"]) + 1

        prompt_parts: list[str] = [
            rules_new_tests,
            common["general_category_rules"],
            (
                f"{format_instructions}"
                "Important for this request:\n"
                "- Propose a genuinely new rule in this category.\n"
                "- Do not repeat a previously rejected idea.\n"
                "- Do not make only a superficial variation of a rejected idea.\n"
                "- If a rejected attempt hit the same path or behavior, choose a meaningfully different one.\n"
                "- Prefer a test that changes the measured score for this category.\n"
            ).strip(),
            (
                f"Category: {common['category']}\n"
                f"Existing explicit bullets in this category: {common['explicit_bullets_count']}\n"
                f"Next bullet number if accepted: {next_bullet_number}"
            ),
            (
                "Current accepted tests for this category:\n"
                f"```python\n{common['current_category_tests']}\n```"
            ),
        ]

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
) -> str:
        """
        Construieste promptul separat pentru cererea metadatelor Rule / Reasoning
        dupa ce testul a fost deja acceptat.
        """
        _, _, rules_rule_and_reasoning = self._get_rules_sections()
        common = self._get_common_category_context(testing_md_path)

        if not accepted_function.strip():
            raise ValueError(
                "accepted_function este necesara pentru construirea promptului de regula si motivare."
            )

        prompt = (
            f"{rules_rule_and_reasoning}\n\n"
            f"{common['general_category_rules']}\n\n"
            f"Category: {common['category']}\n\n"
            f"Accepted test function:\n```python\n{accepted_function}\n```"
        ).strip()

        return prompt


    # ------------------------------------------------------------------
    # Prompt etapa 3 - corectarea unei propuneri invalide
    # ------------------------------------------------------------------

    def build_correction_prompt(
        self,
        testing_md_path: Path,
        validation_error: str,
        proposed_function: str | None = None,
        bullet_index: int | None = None,
    ) -> str:
        """
        Construieste promptul pentru corectarea unei propuneri invalide de test.

        Noua logica:
        - modelul trebuie sa corecteze exact functia respinsa, nu sa schimbe ideea
        - eroarea de validare este data explicit ca restrictie concreta
        - in etapa 2 pastram si testele deja acceptate in categorie
        """
        if not validation_error:
            raise ValueError(
                "validation_error este necesara pentru construirea promptului de corectie."
            )

        common = self._get_common_category_context(testing_md_path)
        format_instructions = self.build_format_instructions()
        proposed_function = proposed_function or "# Empty or unusable previous answer"

        correction_instructions = (
            f"{format_instructions}"
            "You are correcting a previously rejected test.\n"
            "You must correct the same proposed test shown below.\n"
            "Do not switch to another rule.\n"
            "Do not replace it with a different testing idea.\n"
            "Keep the same testing intent, but fix the concrete validation problem.\n"
            "Use the validation error as a strict constraint.\n"
        ).strip()

        if bullet_index is not None:
            rules_initial_tests, _, _ = self._get_rules_sections()
            bullets = self.workspace.extract_testing_rule_bullets(testing_md_path)

            if bullet_index < 0 or bullet_index >= len(bullets):
                raise ValueError(
                    "bullet_index este invalid pentru construirea promptului de corectie."
                )

            explicit_rule_text = bullets[bullet_index]

            prompt_parts = [
                rules_initial_tests,
                common["general_category_rules"],
                correction_instructions,
                (
                    f"Category: {common['category']}\n"
                    "You are correcting a previous invalid answer from the initial-tests stage.\n"
                    f"Explicit rule number: {bullet_index + 1}\n"
                    f"Explicit rule text: {explicit_rule_text}"
                ),
                (
                    "Source code to test:\n"
                    f"```python\n{common['source_code']}\n```"
                ),
                (
                    "Previous proposed answer to be corrected:\n"
                    f"```python\n{proposed_function}\n```"
                ),
                f"Validation error:\n{validation_error}",
            ]

            return "\n\n".join(part.strip() for part in prompt_parts if part.strip())

        _, rules_new_tests, _ = self._get_rules_sections()
        next_bullet_number = int(common["explicit_bullets_count"]) + 1

        prompt_parts = [
            rules_new_tests,
            common["general_category_rules"],
            correction_instructions,
            (
                f"Category: {common['category']}\n"
                "You are correcting a previous invalid answer from the new-tests stage.\n"
                f"Existing explicit bullets in this category: {common['explicit_bullets_count']}\n"
                f"Next bullet number if accepted: {next_bullet_number}"
            ),
            (
                "Current accepted tests for this category:\n"
                f"```python\n{common['current_category_tests']}\n```"
            ),
            (
                "Source code to test:\n"
                f"```python\n{common['source_code']}\n```"
            ),
            (
                "Previous proposed answer to be corrected:\n"
                f"```python\n{proposed_function}\n```"
            ),
            f"Validation error:\n{validation_error}",
        ]

        return "\n\n".join(part.strip() for part in prompt_parts if part.strip())


    # ------------------------------------------------------------------
    # Metoda unica de intrare folosita de orchestrator
    # ------------------------------------------------------------------

    def build_prompt(
        self,
        state: int,
        testing_md_path: Path,
        bullet_index: int | None = None,
        proposed_function: str | None = None,
        validation_error: str | None = None,
        accepted_function: str | None = None,
        failed_attempts: list[tuple[str, str]] | None = None,
    ) -> str:
        """
        Construieste promptul potrivit in functie de starea curenta a fluxului.

        Nou:
        - failed_attempts este folosit in etapa 2 pentru a evita repetarea
        propunerilor deja respinse.
        """
        states = self.config.states

        if state == states.TESTE_INITIALE:
            if bullet_index is None:
                raise ValueError("bullet_index este necesar in starea TESTE_INITIALE.")
            return self.build_initial_tests_prompt(
                testing_md_path=testing_md_path,
                bullet_index=bullet_index,
            )

        if state == states.TESTE_NOI:
            return self.build_new_tests_prompt(
                testing_md_path=testing_md_path,
                failed_attempts=failed_attempts,
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
            )

        raise ValueError("Stare necunoscuta pentru construirea promptului.")


    # ------------------------------------------------------------------
    # Utilitare de inspectie si debug
    # ------------------------------------------------------------------

    def build_prompt_preview(
        self,
        state: int,
        testing_md_path: Path,
        bullet_index: int | None = None,
        proposed_function: str | None = None,
        validation_error: str | None = None,
        accepted_function: str | None = None,
        failed_attempts: list[tuple[str, str]] | None = None,
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
        )

        compact_prompt = full_prompt.replace("\n", " ").strip()
        if len(compact_prompt) <= preview_length:
            return compact_prompt

        return compact_prompt[:preview_length] + "..."
    

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

        trimmed_attempts = failed_attempts[-max_items:]
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