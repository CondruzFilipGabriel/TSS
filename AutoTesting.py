from __future__ import annotations
import hashlib
import re

"""
AutoTesting.py

Rol
---
Acest fisier este orchestratorul principal al framework-ului de generare
automata de teste cu Ollama. El coordoneaza toate componentele extrase in
module separate si ruleaza fluxul complet al aplicatiei.

Flux general
------------
1. Verificare initiala a structurii proiectului
2. Etapa 1:
   - generarea testelor initiale pe baza bullet-urilor explicite din
     fisierele testing_*.md
3. Etapa 2:
   - cautarea unor teste noi, dincolo de bullet-urile existente, pentru
     fiecare categorie
4. Etapa 3:
   - sintetizarea unor reguli care sa caracterizeze testele noi propuse, 
   care sa fie adaugate in fisierele testing_*.md corespunzatoare claselor
   de teste extinse prin testele create 
5. Logarea regulilor acceptate
6. Arhivarea artefactelor finale
7. Afisarea in terminal a regulilor adaugate in sesiunea curenta

Observatii importante
---------------------
1. Limita de timp pentru etapa 2 include doar timpul de generare disponibil
   AI. Timpul de validare si evaluare a performantei nu sunt luate in 
   considerare.

4. Daca o propunere noua este acceptata in etapa 2, timpul AI pentru categoria
   respectiva este resetat la valoareea initiala.
"""

from pathlib import Path

from Archive import ArchiveManager
from Config import AppConfig
from Logger import Logger
from OllamaClient import OllamaClient
from PromptBuilder import PromptBuilder
from ResponseParser import ResponseParser
from TestValidator import TestValidator
from TestsPerformance import PerformanceScores, TestsPerformance
from WorkspaceManager import WorkspaceManager
from Cleanup import CleanupManager


class AutoTesting:
    """
    Orchestratorul principal al framework-ului de generare automata de teste.

    Responsabilitati:
    - initializeaza toate componentele
    - valideaza structura initiala a proiectului
    - ruleaza etapa 1 si etapa 2
    - decide acceptarea sau respingerea propunerilor
    - logheaza regulile acceptate
    - arhiveaza artefactele finale
    """

    def __init__(
        self,
        debugging_enabled: bool = False,
        print_debug: bool = True,
    ) -> None:
        """
        Initializeaza configurarea si toate componentele framework-ului.

        Parametri:
        - debugging_enabled: activeaza logurile tehnice in fisiere
        - print_debug: afiseaza mesajele de debug in terminal
        """
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

        # Starea curenta a fluxului.
        self.state: int = self.config.states.TESTE_INITIALE

        # Numarul de reguli noi acceptate in etapa 2.
        self.numar_reguli_adaugate: int = 0

        # Fisierele testing_*.md gasite in proiect.
        self.fisiere_testing_md: list[Path] = []

        # Mapare de forma:
        # { "testing_structural.md": "test_structural.py", ... }
        self.fisiere_testing: dict[str, str] = {}

        # Istoric de incercari respinse pe categorie.
        # Forma:
        # {
        #   "functional": [(function_code, rejection_reason), ...],
        #   "structural": [(function_code, rejection_reason), ...],
        # }
        self.failed_attempts_by_category: dict[str, list[tuple[str, str]]] = {}

        # Hash-urile propunerilor deja respinse in etapa 2, pentru a evita
        # rescoring-ul repetat al aceleiasi functii.
        # Forma:
        # {
        #   "functional": {"<sha256>", ...},
        #   "structural": {"<sha256>", ...},
        # }
        self.rejected_hashes_by_category: dict[str, set[str]] = {}


    # ------------------------------------------------------------------
    # Initializare si verificari initiale
    # ------------------------------------------------------------------

    def verifica_conditii_initiale(self) -> None:
        """
        Verifica structura initiala minima a proiectului si initializeaza
        artefactele de lucru necesare.
        """
        self.logger.console_step("verific existenta conditiilor de rulare")
        self.workspace.validate_initial_project_structure()

        self.fisiere_testing_md = self.workspace.get_testing_md_files()
        self.fisiere_testing = self.workspace.build_testing_file_mapping()

        self.logger.debug(
            f"Conditiile initiale sunt valide. Model Ollama: {self.config.ollama.model}"
        )


    # ------------------------------------------------------------------
    # Helpers pentru scoruri
    # ------------------------------------------------------------------

    def get_current_scores(
        self,
        selected_test_files: list[str] | None = None,
    ) -> PerformanceScores:
        """
        Returneaza scorurile curente ale suitei de teste pentru fisierele selectate.
        """
        return self.tests_performance.get_current_scores(selected_test_files)


    def format_scores_for_debug(self, scores: PerformanceScores) -> str:
        """
        Formateaza scorurile pentru afisare in debug.
        """
        return self.tests_performance.format_scores_for_debug(scores)

    # ------------------------------------------------------------------
    # Solicitarea unei functii valide catre model
    # ------------------------------------------------------------------

    def solicita_functie_valida(
        self,
        testing_md_path: Path,
        bullet_index: int | None = None,
        remaining_ai_budget_sec: float | None = None,
        failed_attempts: list[tuple[str, str]] | None = None,
    ) -> tuple[str | None, float]:
        """
        Solicita modelului o functie valida si, daca este necesar, cere
        corectarea ei de mai multe ori.

        Returneaza:
        - function_code valid sau None
        - timpul total consumat de AI pentru aceasta secventa de generare
        - in etapa 2, promptul primeste si incercarile deja respinse
        - la fiecare invalidare, functia respinsa si motivul concret sunt memorate
        pentru categoria curenta
        - motivul concret de validare esuata este logat clar in debug
        """
        current_function_code = ""
        current_validation_error = ""
        ai_time_spent = 0.0
        empty_answers_count = 0
        category = self.workspace.get_category_name_from_testing_md(testing_md_path)
        is_new_tests_stage = bullet_index is None

        if bullet_index is not None:
            self.state = self.config.states.TESTE_INITIALE
        else:
            self.state = self.config.states.TESTE_NOI

        prompt = self.prompt_builder.build_prompt(
            state=self.state,
            testing_md_path=testing_md_path,
            bullet_index=bullet_index,
            failed_attempts=failed_attempts if is_new_tests_stage else None,
        )

        max_total_attempts = self.config.timeouts.max_corectie_attempts + 1

        for attempt_index in range(1, max_total_attempts + 1):
            if (
                remaining_ai_budget_sec is not None
                and ai_time_spent >= remaining_ai_budget_sec
            ):
                self.logger.ai(
                    "limita de timp a expirat inainte de obtinerea unei functii valide."
                )
                return None, ai_time_spent

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

            if is_new_tests_stage:
                function_or_answer_to_remember = (
                    current_function_code.strip()
                    or parsed_response.cleaned_text.strip()
                    or (ollama_response.text or "").strip()
                    or "# Empty or unusable previous answer"
                )
                self.remember_failed_attempt(
                    category=category,
                    function_code=function_or_answer_to_remember,
                    rejection_reason=validation_result.message,
                )

            if (
                empty_answers_count
                > self.config.timeouts.max_empty_answers_consecutive
            ):
                self.logger.ai(
                    "prea multe raspunsuri goale sau inutilizabile de la Ollama."
                )
                return None, ai_time_spent

            if self.validator.is_timeout_error(validation_result.message):
                self.logger.ai(
                    "a aparut un timeout la validare. Propunerea este respinsa."
                )
                return None, ai_time_spent

            if attempt_index >= max_total_attempts:
                self.logger.ai(
                    "a fost atins numarul maxim de tentative de corectie."
                )
                return None, ai_time_spent

            self.logger.ai("validez functia propusa si cer o corectie...")
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


    # ------------------------------------------------------------------
    # Etapa 1 - teste initiale
    # ------------------------------------------------------------------

    def scrie_teste_initiale(self) -> None:
        """
        Etapa 1: genereaza testele initiale pe baza bullet-urilor explicite
        din fiecare fisier testing_*.md.

        In aceasta etapa:
        - orice functie valida este acceptata automat
        - nu se verifica imbunatatirea scorurilor

        Ajustare importanta:
        - contextul AI este resetat o singura data la finalul fiecarei categorii,
        pentru a evita aglomerarea terminalului cu mesaje repetitive
        """
        self.logger.section("Etapa 1:")
        self.logger.console_step("generez testele initiale")

        try:
            for testing_md_path in self.fisiere_testing_md:
                category = self.workspace.get_category_name_from_testing_md(
                    testing_md_path
                )
                self.logger.console_step(f"procesez categoria {category}")

                bullets = self.workspace.extract_testing_rule_bullets(
                    testing_md_path
                )
                if not bullets:
                    continue

                category_test_file = self.workspace.map_testing_md_to_test_py(
                    testing_md_path
                )

                for bullet_index, bullet_text in enumerate(bullets):
                    self.logger.debug(
                        f"AI genereaza un test initial pentru regula: {bullet_text}"
                    )

                    valid_function, _ = self.solicita_functie_valida(
                        testing_md_path=testing_md_path,
                        bullet_index=bullet_index,
                    )

                    if not valid_function:
                        self.logger.debug(
                            "Propunerea initiala nu a putut fi validata. Sar peste acest bullet."
                        )
                        self.workspace.clear_proposal_test_file()
                        continue

                    function_name = self.response_parser.extract_function_name(
                        valid_function
                    )
                    if self.workspace.function_exists_in_file(
                        file_path=category_test_file,
                        function_name=function_name,
                    ):
                        self.logger.debug(
                            f"Propunerea initiala este ignorata deoarece functia {function_name} exista deja."
                        )
                        self.workspace.clear_proposal_test_file()
                        continue

                    self.logger.debug("Propunerea initiala a fost acceptata.")
                    self.workspace.append_function_to_test_file(
                        test_file_path=category_test_file,
                        function_code=valid_function,
                    )
                    self.workspace.clear_proposal_test_file()

                self.ollama_client.reset_context()

            self.workspace.add_final_comment_to_initial_test_files()

        finally:
            self.ollama_client.stop()


    # ------------------------------------------------------------------
    # Etapa 2 - cautarea de teste noi
    # ------------------------------------------------------------------

    def gaseste_teste_noi(self) -> None:
        """
        Etapa 2: cauta teste noi pentru fiecare categorie.

        Reguli:
        - se masoara doar timpul de generatie AI
        - evaluarea se face pe: testele categoriei + test_propunere.py
        - daca o propunere valida imbunatateste categoria, este acceptata
        - daca o propunere este acceptata, limita de timp a AI pe categorie 
        se reseteaza
        - daca se acumuleaza 20 de iteratii consecutive fara imbunatatire,
        cautarea se opreste pentru categoria curenta
        - aceeasi functie deja respinsa nu mai este rescored
        """
        self.logger.section("Etapa 2:")
        self.logger.console_step("caut teste noi care imbunatatesc performanta")

        try:
            for testing_md_path in self.fisiere_testing_md:
                category = self.workspace.get_category_name_from_testing_md(
                    testing_md_path
                )
                self.logger.console_step(f"procesez categoria {category}")

                category_test_file = self.workspace.map_testing_md_to_test_py(
                    testing_md_path
                )
                category_selected_test_files = [category_test_file.name]

                ai_budget_ramas = float(
                    self.config.timeouts.timeout_categorie_ai_sec
                )

                max_iterations_without_improvement = 20
                iterations_without_improvement = 0

                while ai_budget_ramas > 0:
                    self.logger.debug(
                        f"Buget AI ramas pentru {category}: {round(ai_budget_ramas, 2)}s"
                    )
                    self.logger.debug(
                        f"Iteratii consecutive fara imbunatatire pentru {category}: "
                        f"{iterations_without_improvement}/{max_iterations_without_improvement}"
                    )

                    if iterations_without_improvement >= max_iterations_without_improvement:
                        self.logger.warning(
                            f"Categoria {category} este oprita deoarece au fost atinse "
                            f"{max_iterations_without_improvement} iteratii consecutive "
                            f"fara nicio imbunatatire."
                        )
                        break

                    before_scores = self.get_current_scores(category_selected_test_files)
                    category_has_tests = self.tests_performance.has_any_tests(
                        category_selected_test_files
                    )

                    if (
                        category_has_tests
                        and not self.tests_performance.is_pytest_clean(before_scores)
                    ):
                        self.logger.warning(
                            f"Categoria {category} nu poate continua deoarece suita curenta nu este curata la pytest."
                        )
                        break

                    self.logger.debug(
                        f"Scoruri curente pentru categoria {category} ({category_test_file.name}) -> "
                        f"{self.format_scores_for_debug(before_scores)}"
                    )

                    valid_function, ai_consumed = self.solicita_functie_valida(
                        testing_md_path=testing_md_path,
                        bullet_index=None,
                        remaining_ai_budget_sec=ai_budget_ramas,
                        failed_attempts=self.get_failed_attempts_for_category(category),
                    )

                    ai_budget_ramas -= ai_consumed

                    if not valid_function:
                        self.logger.debug(
                            "Nu a fost obtinuta nicio propunere valida in bugetul ramas sau in tentativele disponibile."
                        )
                        iterations_without_improvement += 1

                        if ai_budget_ramas <= 0:
                            break

                        continue

                    function_name = self.response_parser.extract_function_name(
                        valid_function
                    )

                    if self.workspace.function_exists_in_file(
                        file_path=category_test_file,
                        function_name=function_name,
                    ):
                        rejection_reason = (
                            f"Propunerea este respinsa deoarece functia {function_name} "
                            f"exista deja in {category_test_file.name}."
                        )
                        self.logger.debug(rejection_reason)
                        self.remember_failed_attempt(
                            category=category,
                            function_code=valid_function,
                            rejection_reason=rejection_reason,
                        )
                        self.remember_rejected_hash(
                            category=category,
                            function_code=valid_function,
                        )
                        self.workspace.clear_proposal_test_file()
                        self.ollama_client.reset_context()
                        iterations_without_improvement += 1
                        continue

                    if self.has_rejected_hash(category, valid_function):
                        rejection_reason = (
                            "Propunerea este respinsa deoarece aceasta functie a mai fost "
                            "evaluata si respinsa anterior in aceasta categorie."
                        )
                        self.logger.debug(rejection_reason)
                        self.remember_failed_attempt(
                            category=category,
                            function_code=valid_function,
                            rejection_reason=rejection_reason,
                        )
                        self.workspace.clear_proposal_test_file()
                        self.ollama_client.reset_context()
                        iterations_without_improvement += 1
                        continue

                    self.workspace.overwrite_proposal_with_function(valid_function)

                    candidate_selected_test_files = self.build_candidate_selected_test_files(
                        category_test_file_name=category_test_file.name
                    )

                    after_scores = self.get_current_scores(candidate_selected_test_files)

                    self.logger.debug(
                        f"Scoruri candidat pentru categoria {category} "
                        f"({candidate_selected_test_files}) -> "
                        f"{self.format_scores_for_debug(after_scores)}"
                    )

                    should_accept = self.should_accept_stage2_proposal(
                        category_has_tests_before=category_has_tests,
                        before_scores=before_scores,
                        after_scores=after_scores,
                    )

                    if should_accept:
                        self.logger.console_step(
                            f"test nou acceptat in categoria {category}"
                        )

                        self.workspace.append_extension_function_to_test_file(
                            test_file_path=category_test_file,
                            function_code=valid_function,
                        )
                        self.numar_reguli_adaugate += 1

                        rule, reasoning = self.solicita_rule_si_reasoning(
                            testing_md_path=testing_md_path,
                            accepted_function=valid_function,
                        )

                        improvement = self.tests_performance.format_improvement(
                            before_scores=before_scores,
                            after_scores=after_scores,
                        )

                        self.logger.append_rule(
                            category=category,
                            rule=rule,
                            reasoning=reasoning,
                            improvement=improvement,
                        )

                        self.workspace.append_rule_bullet_to_testing_md(
                            testing_md_path=testing_md_path,
                            rule_text=rule,
                        )

                        self.workspace.clear_proposal_test_file()
                        self.ollama_client.reset_context()

                        ai_budget_ramas = float(
                            self.config.timeouts.timeout_categorie_ai_sec
                        )
                        iterations_without_improvement = 0

                        self.logger.debug(
                            f"Bugetul AI pentru {category} a fost resetat dupa acceptarea propunerii."
                        )
                        self.logger.debug(
                            f"Contorul de stagnare pentru {category} a fost resetat la 0."
                        )
                    else:
                        rejection_reason = self.explain_stage2_rejection_reason(
                            category_has_tests_before=category_has_tests,
                            before_scores=before_scores,
                            after_scores=after_scores,
                        )
                        self.logger.debug(rejection_reason)

                        self.remember_failed_attempt(
                            category=category,
                            function_code=valid_function,
                            rejection_reason=rejection_reason,
                        )
                        self.remember_rejected_hash(
                            category=category,
                            function_code=valid_function,
                        )

                        self.workspace.clear_proposal_test_file()
                        self.ollama_client.reset_context()
                        iterations_without_improvement += 1

        finally:
            self.ollama_client.stop()


    def normalize_rule_text(self, rule: str, fallback_rule: str = "") -> str:
        """
        Curata textul regulii inainte de salvarea in testing_*.md si Logs.jsonl.

        Reguli:
        - elimina prefixe redundante
        - elimina spatii inutile
        - foloseste fallback_rule daca regula lipseste sau este prea slaba
        """
        cleaned_rule = (rule or "").strip()
        fallback_rule = (fallback_rule or "").strip()

        for prefix in ("Rule:", "# Rule:"):
            if cleaned_rule.startswith(prefix):
                cleaned_rule = cleaned_rule[len(prefix):].strip()

        weak_rule_values = {
            "",
            "n/a",
            "none",
            "unknown",
            "generic rule",
            "test rule",
            "new test",
            "new accepted test",
        }

        if cleaned_rule.lower() in weak_rule_values:
            cleaned_rule = fallback_rule

        return cleaned_rule


    def normalize_rule_text_for_comparison(self, text: str) -> str:
        """
        Normalizeaza un text de regula pentru comparatii aproximative.

        Pastreaza doar litere si spatii, pentru a putea compara semantic
        formularea curenta cu regulile deja existente.
        """
        lowered = (text or "").lower()
        letters_only = re.sub(r"[^a-zA-Z\s]", " ", lowered)
        compact = re.sub(r"\s+", " ", letters_only).strip()
        return compact


    def contains_forbidden_rule_characters(self, rule: str) -> bool:
        """
        Verifica daca regula contine caractere sau forme interzise.

        Interzicem explicit:
        - cifre
        - underscore
        - backticks
        - paranteze, acolade, paranteze patrate
        - slash-uri
        - operatori sau notatii asemanatoare codului
        - ghilimele
        """
        if not (rule or "").strip():
            return False

        forbidden_pattern = r"[0-9_`\"'()\[\]{}\\/=<>\+\-\*%]"
        return re.search(forbidden_pattern, rule) is not None


    def extract_forbidden_rule_identifiers(
        self,
        testing_md_path: Path,
        accepted_function: str,
    ) -> set[str]:
        """
        Extrage identificatori concreti din codul sursa si din functia acceptata,
        pentru a preveni aparitia lor in regula generalizata.

        Exemple:
        - nume de functie
        - nume de variabile
        - nume de stari / rezultate concrete
        """
        source_code = self.workspace.read_file_under_test_source()
        combined_text = f"{source_code}\n{accepted_function}"

        identifiers = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", combined_text)

        ignored_words = {
            "def",
            "return",
            "if",
            "elif",
            "else",
            "for",
            "while",
            "with",
            "raise",
            "assert",
            "in",
            "and",
            "or",
            "not",
            "true",
            "false",
            "none",
            "import",
            "from",
            "pytest",
            "test",
        }

        result: set[str] = set()
        for identifier in identifiers:
            lowered = identifier.lower()
            if lowered in ignored_words:
                continue
            if len(lowered) <= 2:
                continue
            result.add(lowered)

        return result


    def rule_contains_forbidden_identifiers(
        self,
        rule: str,
        forbidden_identifiers: set[str],
    ) -> bool:
        """
        Verifica daca regula contine identificatori concreti extrasi din scriptul curent.
        """
        normalized_rule = re.findall(r"\b[a-zA-Z_][a-zA-Z_]*\b", (rule or "").lower())

        for token in normalized_rule:
            if token in forbidden_identifiers:
                return True

        return False


    def is_rule_too_similar_to_existing_rules(
        self,
        testing_md_path: Path,
        rule: str,
    ) -> bool:
        """
        Verifica daca regula noua este prea apropiata de una deja existenta
        in fisierul categoriei.

        Heuristica:
        - egalitate dupa normalizare
        - una o contine pe cealalta dupa normalizare
        """
        candidate = self.normalize_rule_text_for_comparison(rule)
        if not candidate:
            return False

        existing_rules = self.workspace.extract_testing_rule_bullets(testing_md_path)

        for existing_rule in existing_rules:
            existing = self.normalize_rule_text_for_comparison(existing_rule)
            if not existing:
                continue

            if candidate == existing:
                return True

            if candidate in existing or existing in candidate:
                return True

        return False


    def validate_rule_and_reasoning_candidate(
        self,
        raw_response: str,
        rule: str,
        reasoning: str,
        testing_md_path: Path,
        accepted_function: str,
    ) -> str:
        """
        Valideaza forma si nivelul de generalizare pentru Rule / Reasoning.

        Returneaza:
        - "Valid" daca raspunsul este acceptabil
        - altfel, un mesaj de reformulare
        """
        nonempty_lines = [
            line.strip()
            for line in (raw_response or "").splitlines()
            if line.strip()
        ]

        if len(nonempty_lines) != 2:
            return (
                "The rule does not satisfy the required form. Rewrite it.\n"
                "Return exactly two non-empty comment lines and nothing else."
            )

        if not nonempty_lines[0].startswith("# Rule:"):
            return (
                "The rule does not satisfy the required form. Rewrite it.\n"
                "The first line must start exactly with '# Rule:'."
            )

        if not nonempty_lines[1].startswith("# Reasoning:"):
            return (
                "The rule does not satisfy the required form. Rewrite it.\n"
                "The second line must start exactly with '# Reasoning:'."
            )

        if not (rule or "").strip():
            return (
                "The rule does not satisfy the required form. Rewrite it.\n"
                "The rule text is empty."
            )

        if not (reasoning or "").strip():
            return (
                "The rule does not satisfy the required form. Rewrite it.\n"
                "The reasoning text is empty."
            )

        if self.contains_forbidden_rule_characters(rule):
            return (
                "The rule does not satisfy the required form. Rewrite it.\n"
                "The rule contains forbidden characters or code-like notation.\n"
                "Do not use digits, underscores, backticks, parentheses, brackets, braces, slashes, quotes, or operator-like symbols.\n"
                "Use a more general wording such as threshold value, zero value, minimum accepted value, maximum rejected value, validation path, default path, override path, accepted outcome, rejected outcome, or special outcome."
            )

        forbidden_identifiers = self.extract_forbidden_rule_identifiers(
            testing_md_path=testing_md_path,
            accepted_function=accepted_function,
        )

        if self.rule_contains_forbidden_identifiers(rule, forbidden_identifiers):
            return (
                "The rule does not satisfy the required form. Rewrite it.\n"
                "The rule still contains file-specific identifiers from the current script.\n"
                "Do not use function names, variable names, class names, or concrete instantiated names from the code.\n"
                "Replace them with semantic abstractions such as analyzed function, numeric parameter, counting parameter, state parameter, input data, parameter combination, threshold value, validation exception, accepted outcome, or execution path."
            )

        if self.is_rule_too_similar_to_existing_rules(
            testing_md_path=testing_md_path,
            rule=rule,
        ):
            return (
                "The rule does not satisfy the required form. Rewrite it.\n"
                "The rule is too close to an existing rule in the same category.\n"
                "Rewrite it in a more general and genuinely distinct form."
            )

        return "Valid"


    def is_weak_generic_rule(self, rule: str) -> bool:
        """
        Detecteaza reguli prea vagi sau prea apropiate de fallback-uri.

        Aceasta nu este o validare dura de forma, ci o euristica pentru a decide
        daca o reformulare este semantic mai buna decat alta.
        """
        normalized = self.normalize_rule_text_for_comparison(rule)

        weak_rules = {
            "",
            "new distinct accepted rule in this category",
            "new distinct rule in this category",
            "new accepted rule in this category",
            "new rule in this category",
            "generic rule",
            "test rule",
            "new rule",
        }

        return normalized in weak_rules
    

    def score_rule_candidate(
        self,
        category: str,
        rule: str,
        reasoning: str,
    ) -> int:
        """
        Atribuie un scor euristic unei perechi Rule / Reasoning.

        Scop:
        - nu blocheaza limbajul prin termeni obligatorii
        - foloseste doar semnale moi pentru a compara doua variante valide
        - prefera reguli mai reprezentative, mai generale si mai reconstructive
        """
        normalized_rule = self.normalize_rule_text_for_comparison(rule)
        normalized_reasoning = self.normalize_rule_text_for_comparison(reasoning)

        if not normalized_rule:
            return -100

        score = 0

        if self.is_weak_generic_rule(rule):
            score -= 10
        else:
            score += 3

        word_count = len(normalized_rule.split())
        if 6 <= word_count <= 24:
            score += 2
        elif word_count < 5:
            score -= 2
        elif word_count > 30:
            score -= 1

        causal_markers = [
            "when",
            "if",
            "before",
            "after",
            "instead",
            "because",
            "produces",
            "triggers",
            "causes",
            "leads to",
            "results in",
        ]
        score += min(
            3,
            sum(1 for marker in causal_markers if marker in normalized_rule),
        )

        if category == "functional":
            functional_markers = [
                "observable",
                "outcome",
                "result",
                "validation",
                "exception",
                "boundary",
                "input",
                "behavior",
                "effect",
            ]
            structural_markers = [
                "branch",
                "condition",
                "loop",
                "path",
                "iteration",
                "control flow",
                "execution path",
            ]

            functional_hits = sum(
                1 for marker in functional_markers if marker in normalized_rule
            )
            structural_hits = sum(
                1 for marker in structural_markers if marker in normalized_rule
            )

            score += min(3, functional_hits)

            if structural_hits > functional_hits + 1:
                score -= 2

        elif category == "structural":
            structural_markers = [
                "branch",
                "condition",
                "loop",
                "path",
                "iteration",
                "execution",
                "control flow",
                "validation path",
                "default path",
                "override path",
            ]
            functional_markers = [
                "observable",
                "outcome",
                "result",
                "exception",
                "boundary",
                "input",
            ]

            structural_hits = sum(
                1 for marker in structural_markers if marker in normalized_rule
            )
            functional_hits = sum(
                1 for marker in functional_markers if marker in normalized_rule
            )

            score += min(3, structural_hits)

            if functional_hits > structural_hits + 1:
                score -= 2

        reasoning_markers = [
            "adds",
            "covers",
            "boundary",
            "validation",
            "branch",
            "path",
            "loop",
            "condition",
            "outcome",
            "exception",
        ]
        if any(marker in normalized_reasoning for marker in reasoning_markers):
            score += 1

        return score


    def choose_better_rule_candidate(
        self,
        testing_md_path: Path,
        first_rule: str,
        first_reasoning: str,
        refined_rule: str,
        refined_reasoning: str,
    ) -> tuple[str, str]:
        """
        Alege varianta mai buna dintre prima regula valida si varianta rafinata.

        Regula:
        - daca varianta rafinata are scor mai bun, o pastram pe ea
        - daca scorurile sunt egale, pastram varianta care nu este slaba generic
        - daca si asa sunt egale, pastram prima varianta valida pentru stabilitate
        """
        category = self.workspace.get_category_name_from_testing_md(testing_md_path)

        first_score = self.score_rule_candidate(
            category=category,
            rule=first_rule,
            reasoning=first_reasoning,
        )
        refined_score = self.score_rule_candidate(
            category=category,
            rule=refined_rule,
            reasoning=refined_reasoning,
        )

        if refined_score > first_score:
            return refined_rule, refined_reasoning

        if refined_score == first_score:
            first_is_weak = self.is_weak_generic_rule(first_rule)
            refined_is_weak = self.is_weak_generic_rule(refined_rule)

            if first_is_weak and not refined_is_weak:
                return refined_rule, refined_reasoning

        return first_rule, first_reasoning


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
    ) -> tuple[str, str]:
        """
        Cere separat metadatele Rule / Reasoning pentru un test deja acceptat.

        Flux nou:
        1. obtine prima varianta valida formal
        2. reseteaza contextul
        3. cere o versiune mai reprezentativa, mai generala si mai reconstructiva
        4. daca versiunea rafinata este valida si mai buna, o pastreaza
        5. altfel pastreaza prima varianta valida
        """
        fallback_rule = "New distinct accepted rule in this category"
        fallback_reasoning = (
            "The accepted test improved the category and added a useful new case."
        )

        first_raw, first_rule, first_reasoning = self.obtine_rule_si_reasoning_valid(
            testing_md_path=testing_md_path,
            accepted_function=accepted_function,
            refinement_mode=False,
        )

        if not first_rule or not first_reasoning:
            return fallback_rule, fallback_reasoning

        first_rule = self.normalize_rule_text(
            rule=first_rule,
            fallback_rule=fallback_rule,
        )

        self.ollama_client.reset_context()

        refinement_feedback = (
            "Rewrite the previous rule and reasoning into a more representative version.\n"
            "Keep the same testing meaning.\n"
            "Make the rule more general, more category-faithful, and more reconstructive.\n"
            "If another function had similar logic, this rewritten rule should naturally lead to the same kind of test.\n"
            "Do not become vaguer.\n"
            "Do not become more concrete."
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
            fallback_rule=first_rule,
        )

        best_rule, best_reasoning = self.choose_better_rule_candidate(
            testing_md_path=testing_md_path,
            first_rule=first_rule,
            first_reasoning=first_reasoning,
            refined_rule=refined_rule,
            refined_reasoning=refined_reasoning,
        )

        return best_rule, best_reasoning


    # ------------------------------------------------------------------
    # Arhivare si raportare finala
    # ------------------------------------------------------------------

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
        Afiseaza regulile noi acceptate in sesiunea curenta.
        """
        self.logger.console_step("Rezultate finale:")
        self.logger.print_last_added_rules(self.numar_reguli_adaugate)


    def compute_function_hash(self, function_code: str) -> str:
        """
        Construieste un hash stabil pentru o functie de test, astfel incat
        aceeasi propunere sa poata fi recunoscuta chiar daca difera doar prin
        whitespace minor.
        """
        normalized_code = "\n".join(
            line.rstrip()
            for line in (function_code or "").strip().splitlines()
        ).strip()

        return hashlib.sha256(normalized_code.encode("utf-8")).hexdigest()


    def get_failed_attempts_for_category(self, category: str) -> list[tuple[str, str]]:
        """
        Returneaza lista incercarilor respinse deja memorate pentru o categorie.
        """
        return list(self.failed_attempts_by_category.get(category, []))


    def remember_failed_attempt(
        self,
        category: str,
        function_code: str,
        rejection_reason: str,
        max_items_per_category: int = 25,
    ) -> None:
        """
        Memoreaza o incercare respinsa pentru a putea fi data ulterior modelului
        ca exemplu negativ.

        Duplicatele exacte (aceeasi functie + acelasi motiv) sunt ignorate.
        """
        clean_function = (function_code or "").strip()
        clean_reason = (rejection_reason or "").strip()

        if not clean_function:
            clean_function = "# Empty or unusable previous answer"

        if not clean_reason:
            clean_reason = "Rejected without an explicit recorded reason."

        bucket = self.failed_attempts_by_category.setdefault(category, [])
        candidate = (clean_function, clean_reason)

        if candidate in bucket:
            return

        bucket.append(candidate)

        if len(bucket) > max_items_per_category:
            del bucket[:-max_items_per_category]


    def has_rejected_hash(self, category: str, function_code: str) -> bool:
        """
        Verifica daca functia a mai fost respinsa deja in etapa 2 pentru categoria data.
        """
        function_hash = self.compute_function_hash(function_code)
        return function_hash in self.rejected_hashes_by_category.get(category, set())


    def remember_rejected_hash(self, category: str, function_code: str) -> None:
        """
        Salveaza hash-ul unei propuneri respinse in etapa 2, pentru a evita
        re-evaluarea aceleiasi functii.
        """
        function_hash = self.compute_function_hash(function_code)
        bucket = self.rejected_hashes_by_category.setdefault(category, set())
        bucket.add(function_hash)


    def build_candidate_selected_test_files(
        self,
        category_test_file_name: str,
    ) -> list[str]:
        """
        Returneaza lista fisierelor care trebuie evaluate pentru o propunere noua:
        - fisierul categoriei
        - fisierul temporar al propunerii

        Noua logica de acceptare trebuie sa masoare performanta pe:
        testele categoriei + propunerea noua.
        """
        return [
            category_test_file_name,
            self.config.files.proposal_test_file_name,
        ]


    def should_accept_stage2_proposal(
        self,
        category_has_tests_before: bool,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
    ) -> bool:
        """
        Decide daca o propunere din etapa 2 trebuie acceptata.

        Reguli:
        - daca categoria avea deja teste, se aplica criteriul strict actual:
        suita trebuie sa fie curata inainte si dupa, niciun scor sa nu scada,
        iar cel putin un scor sa creasca
        - daca categoria era goala, permitem bootstrap-ul:
        propunerea este acceptata daca noua suita candidat este curata la pytest
        si exista o imbunatatire reala fata de starea 0-score
        (inclusiv cresterea pytest de la 0 la 100)
        """
        if category_has_tests_before:
            return self.tests_performance.has_strict_improvement(
                before_scores=before_scores,
                after_scores=after_scores,
            )

        if not self.tests_performance.is_pytest_clean(after_scores):
            return False

        before_values = (
            before_scores.pytest_score,
            before_scores.coverage_score,
            before_scores.mutation_score,
        )
        after_values = (
            after_scores.pytest_score,
            after_scores.coverage_score,
            after_scores.mutation_score,
        )

        return any(after > before for before, after in zip(before_values, after_values))


    def explain_stage2_rejection_reason(
        self,
        category_has_tests_before: bool,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
    ) -> str:
        """
        Explica de ce o propunere din etapa 2 a fost respinsa.

        Pentru categoriile deja populate folosim explicatia existenta.
        Pentru categoriile goale folosim o explicatie de bootstrap.
        """
        if category_has_tests_before:
            return self.tests_performance.explain_rejection_reason(
                before_scores=before_scores,
                after_scores=after_scores,
            )

        if not self.tests_performance.is_pytest_clean(after_scores):
            return (
                "Propunerea este respinsa deoarece categoria era goala, iar dupa "
                "adaugarea testului candidat suita nu este curata la pytest."
            )

        before_values = (
            before_scores.pytest_score,
            before_scores.coverage_score,
            before_scores.mutation_score,
        )
        after_values = (
            after_scores.pytest_score,
            after_scores.coverage_score,
            after_scores.mutation_score,
        )

        if not any(after > before for before, after in zip(before_values, after_values)):
            return (
                "Propunerea este respinsa deoarece nu reuseste sa stabileasca o baza "
                "mai buna pentru categorie si nu imbunatateste niciun scor."
            )

        return "Propunerea poate fi acceptata."


    # ------------------------------------------------------------------
    # Flux principal
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Ruleaza fluxul complet al framework-ului.
        """
        self.logger.section("Pregatiri initiale:")
        self.cleanup_manager.cleanup_before_run()
        self.verifica_conditii_initiale()
        self.logger.separator()

        self.scrie_teste_initiale()
        self.logger.separator()

        self.gaseste_teste_noi()
        self.logger.separator()

        self.logger.section("Final:")
        self.arhiveaza()
        self.cleanup_manager.cleanup_after_run()
        self.afiseaza_reguli_adaugate()


def main() -> None:
    """
    Punct minim de intrare pentru executie.

    Creeaza orchestratorul si ruleaza intregul flux, raportand erorile
    principale intr-o forma simpla si lizibila.
    """
    try:
        auto_testing = AutoTesting(
            debugging_enabled=True,
            print_debug=True,
        )
        auto_testing.run()
    except (
        FileNotFoundError,
        ValueError,
        RuntimeError,
        OSError,
        Exception,
    ) as error:
        print(error)


if __name__ == "__main__":
    main()