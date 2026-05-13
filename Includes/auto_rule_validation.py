from __future__ import annotations
import re
from pathlib import Path


class AutoRuleValidationMixin:
    def extract_strict_forbidden_rule_terms(
        self,
        testing_md_path: Path,
        accepted_function: str,
    ) -> set[str]:
        """
        Extrage doar termenii concreti care sunt foarte probabil specifici codului:
        - nume de functii definite in sursa sau in test
        - fragmente alfabetice din stringuri concrete

        Aceasta metoda este mai permisiva decat extragerea tuturor identificatorilor,
        pentru a nu respinge inutil termeni generici utili regulii.
        """
        source_code = self.workspace.read_file_under_test_source()
        combined_text = f"{source_code}\n{accepted_function}"

        result: set[str] = set()

        for function_name in re.findall(r"\bdef\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", combined_text):
            for token in re.findall(r"[A-Za-z]+", function_name):
                lowered = token.lower()
                if len(lowered) > 2:
                    result.add(lowered)

        string_matches = re.findall(
            r"(?:'([^']*)'|\"([^\"]*)\")",
            combined_text,
            flags=re.DOTALL,
        )

        for single_quoted, double_quoted in string_matches:
            string_value = single_quoted or double_quoted
            for token in re.findall(r"[A-Za-z]+", string_value):
                lowered = token.lower()
                if len(lowered) > 2:
                    result.add(lowered)

        ignored_terms = {
            "test",
            "rule",
            "reasoning",
            "pytest",
            "raises",
            "value",
            "input",
            "output",
            "condition",
            "decision",
            "behavior",
            "exception",
            "result",
        }

        return {term for term in result if term not in ignored_terms}

    def rule_contains_strict_forbidden_terms(
        self,
        rule: str,
        forbidden_terms: set[str],
    ) -> bool:
        """
        Verifica daca regula foloseste termeni concreti extrasi din nume de functii
        sau din stringuri concrete ale codului curent.
        """
        rule_terms = {
            token.lower()
            for token in re.findall(r"\b[A-Za-z]+\b", rule or "")
            if len(token) > 2
        }

        return any(term in rule_terms for term in forbidden_terms)

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
        Valideaza forma minima si nivelul minim de generalizare pentru Rule / Reasoning.

        Validarea este intentionat mai permisiva:
        - pastreaza forma in doua linii
        - blocheaza regulile goale sau generice
        - blocheaza caracterele code-like
        - blocheaza termenii concreti evidenti din nume de functii si stringuri
        """
        nonempty_lines = [
            line.strip()
            for line in (raw_response or "").splitlines()
            if line.strip()
        ]

        if len(nonempty_lines) != 2:
            return (
                "Return exactly two non-empty comment lines.\n"
                "Line one must start with '# Rule:'.\n"
                "Line two must start with '# Reasoning:'."
            )

        if not nonempty_lines[0].startswith("# Rule:"):
            return "Line one must start exactly with '# Rule:'."

        if not nonempty_lines[1].startswith("# Reasoning:"):
            return "Line two must start exactly with '# Reasoning:'."

        cleaned_rule = (rule or "").strip()
        cleaned_reasoning = (reasoning or "").strip()

        if not cleaned_rule:
            return "The rule text is empty. Write one reusable category rule."

        if not cleaned_reasoning:
            return "The reasoning text is empty. Write one concise reason."

        if self.is_weak_generic_rule(cleaned_rule):
            return (
                "The rule is too generic. Write the concrete type of test in general terms, "
                "using the category vocabulary."
            )

        if self.contains_forbidden_rule_characters(cleaned_rule):
            return (
                "The rule contains code-like characters. Use plain English words, spaces, "
                "and simple punctuation only."
            )

        forbidden_terms = self.extract_strict_forbidden_rule_terms(
            testing_md_path=testing_md_path,
            accepted_function=accepted_function,
        )

        if self.rule_contains_strict_forbidden_terms(cleaned_rule, forbidden_terms):
            return (
                "The rule contains concrete terms from the current code. Replace them with "
                "category-level semantic terms."
            )

        if self.is_rule_too_similar_to_existing_rules(
            testing_md_path=testing_md_path,
            rule=cleaned_rule,
        ):
            return (
                "The rule is too close to an existing accepted rule. Write the new testing "
                "idea more distinctly."
            )

        return "Valid"

    def is_weak_generic_rule(self, rule: str) -> bool:
        """
        Detecteaza reguli prea vagi sau fallback-uri care nu trebuie salvate ca
        reguli reale in testing_*.md.
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
            "new test",
            "accepted test",
            "useful new case",
        }

        return normalized in weak_rules
