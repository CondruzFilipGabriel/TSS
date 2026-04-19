from __future__ import annotations
import re

"""
TestValidator.py

Rol
---
Acest fisier valideaza o functie de test propusa de modelul AI, inainte ca
aceasta sa fie acceptata in suita curenta de teste.

Scopul lui este sa separe complet din orchestrator logica de validare, care
include atat verificari statice, cat si verificari dinamice prin pytest.

Ce valideaza
------------
1. Raspunsul contine cod util, nu este gol si nu este inutilizabil.
2. Raspunsul nu contine placeholder-e sau text explicativ interzis.
3. Codul rezultat este Python valid din punct de vedere sintactic.
4. Exista exact o singura functie al carei nume incepe cu test_.
5. Nu exista cod suplimentar in afara acelei functii.
6. Functia poate fi executata tehnic prin pytest intr-un fisier temporar.

Observatii importante
---------------------
1. Acest modul nu parseaza raspunsul brut. Pentru asta foloseste ResponseParser.
2. Acest modul nu scrie teste acceptate in fisierele finale. El doar valideaza.
3. Acest modul considera valida o functie doar daca aceasta trece la pytest.
   Testele care pica la rulare sunt considerate invalide si nu trebuie
   acceptate in suita finala.
4. Timeout-ul de validare este luat din Config.py.
"""

import ast
import subprocess
from dataclasses import dataclass

from Config import AppConfig
from Logger import Logger
from ResponseParser import ParsedResponse, ResponseParser
from WorkspaceManager import WorkspaceManager


@dataclass(frozen=True)
class ValidationResult:
    """
    Reprezinta rezultatul complet al unei validari.

    Campuri:
    - is_valid: True daca propunerea este considerata valida
    - message: mesajul final de validare
    - parsed_response: raspunsul parsat, util pentru etapele urmatoare
    """

    is_valid: bool
    message: str
    parsed_response: ParsedResponse


class TestValidator:
    """
    Valideaza functiile de test propuse de modelul AI.

    Parametri:
    - config: configurarea centrala a aplicatiei
    - logger: logger-ul folosit pentru debug si erori
    - workspace: managerul fisierelor proiectului
    - response_parser: parserul folosit pentru extragerea functiei si a
      metadatelor din raspunsul AI
    """

    def __init__(
        self,
        config: AppConfig,
        logger: Logger,
        workspace: WorkspaceManager,
        response_parser: ResponseParser,
    ) -> None:
        self.config = config
        self.logger = logger
        self.workspace = workspace
        self.response_parser = response_parser
        

    # ------------------------------------------------------------------
    # Verificari de baza pe textul raspunsului
    # ------------------------------------------------------------------

    def contains_forbidden_placeholders(self, text: str) -> bool:
        """
        Verifica daca textul contine placeholder-e sau expresii interzise.

        Lista este luata din configurarea centrala, pentru a ramane compatibila
        cu logica initiala din AutoTesting.py.
        """
        lower_text = text.lower()

        for pattern in self.config.test_rules.placeholder_patterns:
            if pattern.lower() in lower_text:
                return True

        return False


    def build_placeholder_error_message(self) -> str:
        """
        Returneaza mesajul standard pentru raspunsuri care contin placeholder-e
        sau text explicativ interzis.
        """
        return (
            "The response still contains placeholders or explanatory text. "
            "Use the exact concrete names and values from the provided source code."
        )


    # ------------------------------------------------------------------
    # Validare structurala prin AST
    # ------------------------------------------------------------------

    def parse_python_ast(self, function_code: str) -> ast.Module:
        """
        Parseaza codul functiei si returneaza arborele AST.

        Ridica SyntaxError daca textul nu este Python valid.
        """
        return ast.parse(function_code)


    def extract_test_functions_from_ast(self, tree: ast.Module) -> list[ast.FunctionDef]:
        """
        Extrage toate functiile al caror nume incepe cu test_ din arborele AST.
        """
        return [
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
        ]


    def validate_ast_structure(self, function_code: str) -> str:
        """
        Valideaza structura AST a functiei propuse.

        Verificari:
        - codul este parsabil Python
        - exista cel putin o functie test_*
        - exista exact o singura functie test_*
        - modulul contine exact un singur nod si acesta este functia test_*

        Returneaza:
        - "Valid" daca structura este buna
        - un mesaj de eroare altfel
        """
        try:
            tree = self.parse_python_ast(function_code)
        except SyntaxError as error:
            return f"SyntaxError: {error}"

        test_functions = self.extract_test_functions_from_ast(tree)

        if len(test_functions) == 0:
            return (
                "The provided text does not contain any test function "
                "whose name starts with test_."
            )

        if len(test_functions) > 1:
            return (
                "The provided text contains multiple test functions. "
                "Only one test_* function is allowed."
            )

        if len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef):
            return (
                "The provided text must contain exactly one test function "
                "and no additional code."
            )

        return "Valid"


    # ------------------------------------------------------------------
    # Validare dinamica prin pytest
    # ------------------------------------------------------------------

    def _build_validation_file_content(self, function_code: str) -> str:
        """
        Construieste continutul fisierului temporar folosit pentru validare.

        Se adauga importurile standard, apoi functia curatata.
        """
        imports = self.config.test_rules.importuri_teste
        return imports.rstrip() + "\n\n" + function_code.strip() + "\n"


    def _run_pytest_for_single_function(self, function_code: str) -> str:
        """
        Ruleaza pytest pentru functia propusa, intr-un fisier temporar.

        Regula:
        - return code 0 = testul trece -> valid
        - orice alt return code = invalid

        Diferenta fata de varianta veche:
        - mesajul de eroare este comprimat si curatat pentru a fi mai util
        in promptul de corectie
        """
        function_name = self.response_parser.extract_function_name(function_code)
        validation_temp_file = self.config.paths.validate_temp_file

        if not function_name:
            return (
                "The provided text does not contain any test function "
                "whose name starts with test_."
            )

        try:
            file_content = self._build_validation_file_content(function_code)
            self.workspace.write_text(validation_temp_file, file_content)

            command = [
                "python3",
                "-m",
                "pytest",
                "-q",
                f"{validation_temp_file.name}::{function_name}",
                "--maxfail=1",
            ]

            result = subprocess.run(
                command,
                cwd=self.config.paths.current_dir,
                capture_output=True,
                text=True,
                timeout=self.config.timeouts.timeout_sec,
            )

            output = (result.stdout or "") + (result.stderr or "")

            if result.returncode == 0:
                return "Valid"

            return self._extract_pytest_validation_message(
                pytest_output=output,
                function_name=function_name,
            )

        except subprocess.TimeoutExpired:
            return (
                f"TimeoutError: the test did not finish within "
                f"{self.config.timeouts.timeout_sec} seconds."
            )
        finally:
            if validation_temp_file.exists():
                validation_temp_file.unlink()


    # ------------------------------------------------------------------
    # Validare completa
    # ------------------------------------------------------------------

    def validate_parsed_response(self, parsed_response: ParsedResponse) -> ValidationResult:
        """
        Valideaza un raspuns deja parsat.

        Etape:
        1. verificare functie existenta
        2. verificare placeholder-e
        3. validare AST
        4. validare prin pytest

        Returneaza un ValidationResult complet.
        """
        function_code = parsed_response.function_code

        if not function_code:
            return ValidationResult(
                is_valid=False,
                message="The response does not contain a valid test function.",
                parsed_response=parsed_response,
            )

        if self.contains_forbidden_placeholders(function_code):
            return ValidationResult(
                is_valid=False,
                message=self.build_placeholder_error_message(),
                parsed_response=parsed_response,
            )

        ast_validation_message = self.validate_ast_structure(function_code)
        if ast_validation_message != "Valid":
            return ValidationResult(
                is_valid=False,
                message=ast_validation_message,
                parsed_response=parsed_response,
            )

        pytest_validation_message = self._run_pytest_for_single_function(function_code)
        if pytest_validation_message != "Valid":
            return ValidationResult(
                is_valid=False,
                message=pytest_validation_message,
                parsed_response=parsed_response,
            )

        return ValidationResult(
            is_valid=True,
            message="Valid",
            parsed_response=parsed_response,
        )


    def validate_response_text(self, raw_text: str) -> ValidationResult:
        """
        Parseaza si valideaza complet un raspuns brut primit de la model.

        Aceasta este metoda cea mai utila pentru orchestrator.
        """
        parsed_response = self.response_parser.parse_response(raw_text)
        return self.validate_parsed_response(parsed_response)

    def validate_function_code(self, function_code: str) -> str:
        """
        Metoda de compatibilitate cu stilul vechi din AutoTesting.py.

        Primeste direct un cod de functie si returneaza doar mesajul de validare:
        - "Valid"
        - sau mesajul de eroare
        """
        parsed_response = self.response_parser.parse_response(function_code)
        result = self.validate_parsed_response(parsed_response)
        return result.message


    # ------------------------------------------------------------------
    # Utilitare de inspectie
    # ------------------------------------------------------------------

    def is_timeout_error(self, validation_message: str) -> bool:
        """
        Verifica daca mesajul de validare semnaleaza un timeout.
        """
        return "TimeoutError:" in validation_message


    def is_valid(self, raw_text: str) -> bool:
        """
        Returneaza doar verdictul boolean al validarii unui raspuns brut.
        """
        return self.validate_response_text(raw_text).is_valid
    

    def _extract_first_nonempty_lines(
        self,
        text: str,
        max_lines: int = 12,
    ) -> str:
        """
        Extrage primele linii utile dintr-un text lung, eliminand liniile goale.

        Este util pentru a reduce outputul brut din pytest la un mesaj mai scurt,
        usor de folosit in promptul de corectie.
        """
        useful_lines = [
            line.rstrip()
            for line in (text or "").splitlines()
            if line.strip()
        ]

        if not useful_lines:
            return ""

        return "\n".join(useful_lines[:max_lines]).strip()
    

    def _extract_pytest_validation_message(
        self,
        pytest_output: str,
        function_name: str,
    ) -> str:
        """
        Construieste un mesaj scurt si clar din outputul brut al pytest-ului.

        Prioritati:
        - erori de import / colectare
        - exceptii frecvente din rulare
        - assert failure
        - fallback la un excerpt scurt din output

        Scop:
        - mesajul trebuie sa fie suficient de concret pentru ca modelul sa poata
        corecta testul, fara sa primeasca un dump prea mare si zgomotos.
        """
        output = (pytest_output or "").strip()
        if not output:
            return "Pytest validation failed with no output."

        important_patterns = [
            r"(ImportError:.*)",
            r"(ModuleNotFoundError:.*)",
            r"(SyntaxError:.*)",
            r"(IndentationError:.*)",
            r"(NameError:.*)",
            r"(TypeError:.*)",
            r"(ValueError:.*)",
            r"(AttributeError:.*)",
            r"(KeyError:.*)",
            r"(IndexError:.*)",
            r"(AssertionError:.*)",
            r"(Failed:.*)",
        ]

        for pattern in important_patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1).strip()

        if "found no collectors" in output.lower():
            return (
                f"Pytest could not collect the generated test function {function_name}. "
                "Make sure the response contains exactly one valid test_* function."
            )

        excerpt = self._extract_first_nonempty_lines(output, max_lines=12)
        if excerpt:
            return excerpt

        return "Pytest validation failed."