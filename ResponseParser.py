from __future__ import annotations

"""
ResponseParser.py

Rol
---
Acest fisier se ocupa de interpretarea raspunsurilor text venite de la modelul AI.
Scopul lui este sa extraga dintr-un raspuns brut exact partea utila pentru
framework, fara a amesteca aceasta logica in orchestrator sau in validator.

Responsabilitati principale
---------------------------
1. Curatarea raspunsului brut:
   - extragerea codului din blocuri ```python ... ```
   - eliminarea textelor explicative din jurul functiei
   - taierea cozilor evidente de explicatii sau mesaje suplimentare

2. Extragerea unei functii pytest propuse:
   - identificarea functiei care incepe cu def test_
   - pastrarea doar a partii relevante din raspuns

3. Extragerea comentariilor de metadate:
   - # Rule: ...
   - # Reasoning: ...

4. Extragerea informatiei structurale:
   - numele functiei de test
   - regula abstracta
   - motivarea

De ce exista acest modul separat
--------------------------------
In varianta initiala, AutoTesting.py se ocupa direct si de:
- curatarea outputului Ollama
- extragerea functiei din raspuns
- extragerea comentariilor Rule / Reasoning
- extragerea numelui functiei

Aceste operatii formeaza un subsistem distinct, care nu tine nici de:
- orchestrare
- validare AST / pytest
- lucru cu fisiere
- scorare

Prin urmare, merita un modul dedicat.

Observatii
----------
1. Acest modul nu valideaza sintactic functia. Asta va fi responsabilitatea
   TestValidator.py.

2. Acest modul nu scrie fisiere. El doar transforma text in structuri utile.

3. Comentariile Rule si Reasoning sunt tratate ca metadate optionale.
   Daca lipsesc, functia ramane in continuare parsabila.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedResponse:
    """
    Reprezinta rezultatul parsarii unui raspuns AI.

    Campuri:
    - raw_text: raspunsul original, nemodificat
    - cleaned_text: raspunsul dupa curatarea generala
    - function_code: functia pytest extrasa, daca exista
    - metadata_comments: comentariile Rule / Reasoning extrase din functie
    - function_name: numele functiei de test extrase, daca exista
    - rule: regula generala extrasa din comentarii, daca exista
    - reasoning: motivarea extrasa din comentarii, daca exista
    """

    raw_text: str
    cleaned_text: str
    function_code: str
    metadata_comments: str
    function_name: str | None
    rule: str
    reasoning: str


class ResponseParser:
    """
    Parseaza raspunsurile AI si extrage informatia utila framework-ului.

    Clasa este gandita sa fie folosita de orchestrator si de validator:
    - orchestratorul are nevoie de functia propusa si de metadate
    - validatorul are nevoie de functia curatata
    """

    def __init__(self) -> None:
        # Marcatori uzuali dupa care outputul AI devine explicativ sau irelevant
        # pentru framework si trebuie taiat.
        self.stop_markers: tuple[str, ...] = (
            "\nTokens:",
            "\nMake sure",
            "\nHere’s",
            "\nHere's",
            "\nThe test above",
            "\nThis test",
            "\nExplanation:",
        )

    # ------------------------------------------------------------------
    # Curatarea raspunsului brut
    # ------------------------------------------------------------------

    def clean_ollama_output(self, raw_output: str) -> str:
        """
        Curata raspunsul brut primit de la model.

        Corectie importanta:
        - daca modelul pune comentariile # Rule / # Reasoning inainte de functia
        de test, acestea sunt pastrate
        - nu mai taiem direct de la primul 'def test_', deoarece am pierde
        metadatele utile pentru logare
        """
        text = (raw_output or "").strip()

        fenced_block_match = re.search(
            r"```(?:python)?\s*(.*?)```",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if fenced_block_match:
            text = fenced_block_match.group(1).strip()

        # Daca exista comentarii urmate de o functie test_, pastram ambele.
        match_with_comments = re.search(
            r"((?:\s*#.*\n)*)\s*(def\s+test_[\s\S]*)",
            text,
        )
        if match_with_comments:
            comments = match_with_comments.group(1).rstrip()
            code = match_with_comments.group(2).strip()
            text = (comments + "\n" + code).strip() if comments else code
        elif "def test_" in text:
            text = text[text.find("def test_"):]

        for marker in self.stop_markers:
            position = text.find(marker)
            if position != -1:
                text = text[:position].strip()

        text = re.sub(r"[\u2800-\u28FF]", "", text)
        text = re.sub(r"\r", "", text)

        return text.strip()

    # ------------------------------------------------------------------
    # Extragerea functiei si a comentariilor
    # ------------------------------------------------------------------

    def extract_code_and_comments(self, text: str) -> tuple[str, str]:
        """
        Extrage:
        - codul functiei pytest
        - comentariile de metadate Rule / Reasoning

        Corectie importanta:
        - accepta comentariile de metadate atat inainte de functia test,
        cat si la inceputul corpului functiei
        - astfel, parserul devine compatibil cu outputul real generat de model
        """
        cleaned_text = self.clean_ollama_output(text)

        if not cleaned_text:
            return "", ""

        lines = cleaned_text.splitlines()

        metadata_comments: list[str] = []
        function_start_index: int | None = None

        # 1. Cautam mai intai comentariile de metadate plasate inainte de functie.
        for index, line in enumerate(lines):
            stripped_line = line.strip()

            if re.match(r"^def\s+test_[A-Za-z0-9_]+\s*\(", stripped_line):
                function_start_index = index
                break

            if re.match(r"^#\s*(Rule|Reasoning)\s*:", stripped_line):
                metadata_comments.append(stripped_line)
            elif stripped_line.startswith("#") and metadata_comments:
                metadata_comments.append(stripped_line)
            elif stripped_line == "":
                continue
            else:
                # Ignoram alte linii nerelevante pana la functie.
                continue

        if function_start_index is None:
            return "", "\n".join(metadata_comments).strip()

        function_code = "\n".join(lines[function_start_index:]).strip()

        # 2. Daca nu am gasit comentariile inainte de functie, cautam si in corp.
        if not metadata_comments:
            function_lines = function_code.splitlines()

            if len(function_lines) >= 2:
                for line in function_lines[1:]:
                    if re.match(r"^\s*#\s*(Rule|Reasoning)\s*:", line):
                        metadata_comments.append(line.strip())
                    elif re.match(r"^\s*#\s*", line) and metadata_comments:
                        metadata_comments.append(line.strip())
                    else:
                        break

        return function_code, "\n".join(metadata_comments).strip()

    def extract_function_name(self, function_code: str) -> str | None:
        """
        Extrage numele functiei pytest de forma test_* din codul unei functii.

        Daca functia nu poate fi identificata, returneaza None.
        """
        match = re.search(r"def\s+(test_[A-Za-z0-9_]+)\s*\(", function_code)
        if match:
            return match.group(1)
        return None

    # ------------------------------------------------------------------
    # Extragerea metadatelor Rule / Reasoning
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Parsare completa
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Utilitare de comoditate
    # ------------------------------------------------------------------

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