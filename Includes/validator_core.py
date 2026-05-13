from __future__ import annotations
from Includes.validator_models import ValidationResult



class ValidatorCoreMixin:
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
