from __future__ import annotations
from pathlib import Path
import re


class WorkspaceRulesMixin:
    def get_main_header_positions(self, markdown_path: Path) -> list[int]:
        """
        Returneaza pozitiile liniilor care incep cu '# ' intr-un fisier markdown.
        """
        return [
            index
            for index, line in enumerate(self.read_lines(markdown_path))
            if line.startswith("# ")
        ]

    def extract_section_after_header(
        self,
        markdown_path: Path,
        header_index: int,
        until_next_header: bool = True,
    ) -> str:
        """
        Extrage textul de dupa header-ul cu indexul dat.

        Exemplu:
        - header_index = 0 -> textul de dupa primul '# '
        - header_index = 1 -> textul de dupa al doilea '# '

        Daca until_next_header este True, sectiunea se opreste la urmatorul
        header principal '# '. Daca este False, merge pana la finalul fisierului.
        """
        lines = self.read_lines(markdown_path)
        header_positions = self.get_main_header_positions(markdown_path)

        if header_index >= len(header_positions):
            return ""

        start = header_positions[header_index] + 1
        end = len(lines)

        if until_next_header and header_index + 1 < len(header_positions):
            end = header_positions[header_index + 1]

        return "\n".join(lines[start:end]).strip()

    def extract_general_category_rules(self, markdown_path: Path) -> str:
        """
        Extrage regulile generale ale unei categorii din fisierul testing_*.md.

        Logica:
        - se ia textul dintre primul header '# ' si primul bullet numerotat
        """
        lines = self.read_lines(markdown_path)
        start = None
        end = len(lines)

        for index, line in enumerate(lines):
            if line.startswith("# "):
                start = index + 1
                break

        if start is None:
            return ""

        for index in range(start, len(lines)):
            stripped = lines[index].strip()
            if re.match(r"^\d+\.", stripped) or re.match(r"^-\s+", stripped):
                end = index
                break

        return "\n".join(lines[start:end]).strip()

    def extract_testing_rule_bullets(self, markdown_path: Path) -> list[str]:
        """
        Extrage instructiunile explicite dintr-un fisier testing_*.md.

        Formatul recomandat este numerotat:
        - '1. Make one test ...'

        Pentru compatibilitate, accepta si bullets simple:
        - '- Make one test ...'
        """
        bullets: list[str] = []

        for line in self.read_lines(markdown_path):
            stripped = line.strip()

            numbered_match = re.match(r"^\d+\.\s*(.+)$", stripped)
            if numbered_match:
                bullets.append(numbered_match.group(1).strip())
                continue

            dash_match = re.match(r"^-\s+(.+)$", stripped)
            if dash_match:
                bullets.append(dash_match.group(1).strip())

        return bullets

    def count_testing_rule_bullets(self, markdown_path: Path) -> int:
        """
        Returneaza numarul instructiunilor explicite dintr-un fisier testing_*.md.
        """
        return len(self.extract_testing_rule_bullets(markdown_path))

    def append_rule_bullet_to_testing_md(
        self,
        testing_md_path: Path,
        rule_text: str,
    ) -> None:
        """
        Adauga un nou bullet numerotat la finalul sectiunii de reguli explicite
        din fisierul testing_*.md.

        Comportament:
        - numerotarea continua automat dupa ultimul bullet existent
        - evita adaugarea duplicatelor exacte
        - pastreaza restul continutului fisierului
        - nu introduce linii goale suplimentare intre bullet-uri
        """
        normalized_rule = (rule_text or "").strip()
        if not normalized_rule:
            return

        lines = self.read_lines(testing_md_path)
        existing_bullets = self.extract_testing_rule_bullets(testing_md_path)

        if normalized_rule in existing_bullets:
            self.logger.debug(
                f"Regula exista deja in {testing_md_path.name}: {normalized_rule}"
            )
            return

        next_bullet_number = len(existing_bullets) + 1
        new_bullet_line = f"{next_bullet_number}. {normalized_rule}"

        bullet_line_indexes = [
            index
            for index, line in enumerate(lines)
            if re.match(r"^\d+\.\s+.+$", line.strip()) or re.match(r"^-\s+.+$", line.strip())
        ]

        if bullet_line_indexes:
            insert_index = bullet_line_indexes[-1] + 1
        else:
            insert_index = len(lines)

        new_lines = list(lines)
        new_lines.insert(insert_index, new_bullet_line)

        self.write_text(testing_md_path, "\n".join(new_lines).rstrip() + "\n")

        self.logger.debug(
            f"A fost adaugata regula noua in {testing_md_path.name}: {new_bullet_line}"
        )
