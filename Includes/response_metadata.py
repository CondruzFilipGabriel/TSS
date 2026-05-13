from __future__ import annotations
import re
from Includes.response_models import ParsedResponse


class ResponseMetadataMixin:
    def extract_function_name(self, function_code: str) -> str | None:
        """
        Extrage numele functiei pytest de forma test_* din codul unei functii.

        Daca functia nu poate fi identificata, returneaza None.
        """
        match = re.search(r"def\s+(test_[A-Za-z0-9_]+)\s*\(", function_code)
        if match:
            return match.group(1)
        return None

    def extract_rule_and_reasoning_from_comments(
        self,
        metadata_comments: str,
    ) -> tuple[str, str]:
        """
        Parseaza comentariile de metadate si extrage:
        - regula
        - motivarea

        Format acceptat:
            # Rule: ...
            # Reasoning: ...

        Daca exista mai multe linii Reasoning, ele sunt concatenate cu newline.
        """
        rule = ""
        reasoning = ""

        for line in metadata_comments.splitlines():
            cleaned_line = re.sub(r"^\s*#\s*", "", line).strip()
            lower_line = cleaned_line.lower()

            if lower_line.startswith("rule:"):
                rule = cleaned_line.split(":", 1)[1].strip()
            elif lower_line.startswith("reasoning:"):
                text = cleaned_line.split(":", 1)[1].strip()
                reasoning = (
                    (reasoning + "\n" + text).strip()
                    if reasoning
                    else text
                )

        return rule, reasoning

    def parse_response(self, raw_text: str) -> ParsedResponse:
        """
        Parseaza complet un raspuns AI si returneaza toate informatiile utile.

        Foloseste acelasi text curatat pentru:
        - extragerea functiei
        - extragerea comentariilor
        - extragerea numelui functiei
        - extragerea regulii si motivarii
        """
        cleaned_text = self.clean_ollama_output(raw_text)
        function_code, metadata_comments = self.extract_code_and_comments(cleaned_text)
        function_name = self.extract_function_name(function_code)
        rule, reasoning = self.extract_rule_and_reasoning_from_comments(
            metadata_comments
        )

        return ParsedResponse(
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            function_code=function_code,
            metadata_comments=metadata_comments,
            function_name=function_name,
            rule=rule,
            reasoning=reasoning,
        )

    def has_test_function(self, text: str) -> bool:
        """
        Verifica rapid daca textul contine aparent o functie test_*.
        """
        cleaned_text = self.clean_ollama_output(text)
        return re.search(r"\bdef\s+test_[A-Za-z0-9_]+\s*\(", cleaned_text) is not None

    def is_empty_or_unusable(self, text: str) -> bool:
        """
        Verifica daca un raspuns este gol sau nu contine cod util parsabil.

        Aceasta metoda este utila pentru filtrarea raspunsurilor complet goale
        sau evident nefolositoare, inainte de validarea mai stricta.
        """
        if not (text or "").strip():
            return True

        parsed = self.parse_response(text)
        return not parsed.function_code.strip()
