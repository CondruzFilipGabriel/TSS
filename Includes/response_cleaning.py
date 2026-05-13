from __future__ import annotations
import re


class ResponseCleaningMixin:
    def _extract_metadata_comments_before_code_block(self, text: str) -> str:
        """
        Pastreaza comentariile de metadate scrise inaintea unui bloc ```python.

        Unele raspunsuri AI pun # Rule / # Reasoning inaintea blocului de cod,
        iar curatarea simpla a fence-ului ar pierde aceste informatii.
        """
        before_fence = text.split("```", 1)[0]
        metadata_lines: list[str] = []

        for line in before_fence.splitlines():
            stripped = line.strip()
            if re.match(r"^#\s*(Rule|Reasoning|Explanation)\s*:", stripped):
                metadata_lines.append(stripped)
            elif stripped.startswith("#") and metadata_lines:
                metadata_lines.append(stripped)

        return "\n".join(metadata_lines).strip()

    def clean_ollama_output(self, raw_output: str) -> str:
        """
        Curata raspunsul brut primit de la model.

        Pastreaza, cand exista, comentariile # Rule / # Reasoning si functia
        pytest generata. Indeparteaza explicatiile libere, fence-urile Markdown
        si caracterele braille folosite uneori de terminale/progrese.
        """
        text = (raw_output or "").strip()

        metadata_before_fence = self._extract_metadata_comments_before_code_block(text)
        fenced_block_match = re.search(
            r"```(?:python)?\s*(.*?)```",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
        if fenced_block_match:
            code_inside_fence = fenced_block_match.group(1).strip()
            text = (
                metadata_before_fence + "\n" + code_inside_fence
                if metadata_before_fence
                else code_inside_fence
            ).strip()

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

    def extract_code_and_comments(self, text: str) -> tuple[str, str]:
        """
        Extrage codul functiei pytest si comentariile de metadate.
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

            if re.match(r"^#\s*(Rule|Reasoning|Explanation)\s*:", stripped_line):
                metadata_comments.append(stripped_line)
            elif stripped_line.startswith("#") and metadata_comments:
                metadata_comments.append(stripped_line)
            elif stripped_line == "":
                continue
            else:
                continue

        if function_start_index is None:
            return "", "\n".join(metadata_comments).strip()

        function_code = "\n".join(lines[function_start_index:]).strip()

        # 2. Daca nu am gasit comentariile inainte de functie, cautam si in corp.
        if not metadata_comments:
            function_lines = function_code.splitlines()

            if len(function_lines) >= 2:
                for line in function_lines[1:]:
                    if re.match(r"^\s*#\s*(Rule|Reasoning|Explanation)\s*:", line):
                        metadata_comments.append(line.strip())
                    elif re.match(r"^\s*#\s*", line) and metadata_comments:
                        metadata_comments.append(line.strip())
                    else:
                        break

        return function_code, "\n".join(metadata_comments).strip()
