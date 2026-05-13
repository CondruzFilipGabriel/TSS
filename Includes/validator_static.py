from __future__ import annotations
import ast
import re


class ValidatorStaticMixin:
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
