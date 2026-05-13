from __future__ import annotations
import re


class AutoRuleNormalizationMixin:
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
        Verifica daca regula contine caractere care tind sa transforme regula
        intr-o formulare concreta, numerica sau asemanatoare codului.

        Permitem punctuatie naturala simpla:
        - virgula
        - punct
        - punct si virgula
        - doua puncte
        - liniuta
        """
        if not (rule or "").strip():
            return False

        forbidden_pattern = r"[0-9_`\"'()\[\]{}\\/<>+=*%]"
        if re.search(forbidden_pattern, rule):
            return True

        code_like_pattern = r"(==|!=|<=|>=|->|=>|\+\+|--)"
        return re.search(code_like_pattern, rule) is not None
