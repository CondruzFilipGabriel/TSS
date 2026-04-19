from __future__ import annotations

"""
WorkspaceManager.py

Rol
---
Acest fisier gestioneaza artefactele de lucru ale framework-ului de generare
automata de teste. El centralizeaza operatiile pe fisierele proiectului,
astfel incat orchestratorul sa nu mai lucreze direct cu detalii de I/O.

Scopurile principale sunt:
- citirea si scrierea fisierelor text ale proiectului
- identificarea fisierelor testing_*.md
- maparea dintre testing_<categorie>.md si test_<categorie>.py
- initializarea fisierelor de test lipsa
- gestionarea fisierului temporar test_propunere.py
- adaugarea de functii in fisierele de test
- verificarea existentei unei functii intr-un fisier
- extragerea informatiilor relevante din fisierele markdown de reguli

De ce exista acest modul separat
--------------------------------
In varianta initiala, AutoTesting.py se ocupa direct de:
- citirea textului din fisiere
- scrierea de fisiere
- listarea fisierelor testing_*.md
- adaugarea importurilor standard in test files
- golirea fisierului test_propunere.py
- extragerea regulilor si a bullet-urilor din fisierele markdown
- verificarea existentei unei functii in fisierele test_*.py

Aceasta combinatie ingreuneaza mentenanta si testarea. Prin extragerea acestor
responsabilitati in WorkspaceManager.py:
- AutoTesting.py devine un orchestrator mai curat
- logica de acces la fisiere devine reutilizabila
- parsarea fisierelor markdown devine centralizata

Observatii
----------
1. Acest modul nu se ocupa de arhivare. Arhivarea va fi mutata in Archive.py.
2. Acest modul nu se ocupa de logging. Logging-ul va fi tratat de Logger.py.
3. Acest modul nu se ocupa de validarea raspunsurilor AI sau de scorare.
"""

import re
from pathlib import Path

from Config import AppConfig
from Logger import Logger


class WorkspaceManager:
    """
    Gestioneaza toate fisierele si textele de lucru ale framework-ului.

    Responsabilitati principale:
    - acces la fisierele proiectului
    - initializare fisiere de test
    - operatii pe test_propunere.py
    - adaugare functii in fisierele de test
    - parsare de baza pentru fisierele testing_*.md si Rules.md

    Parametri:
    - config: configurarea centrala a aplicatiei
    - logger: logger-ul folosit pentru mesaje de debug si avertizari
    """

    def __init__(self, config: AppConfig, logger: Logger) -> None:
        self.config = config
        self.logger = logger

    # ------------------------------------------------------------------
    # Helpers generali pentru fisiere text
    # ------------------------------------------------------------------

    def read_text(self, path: Path) -> str:
        """
        Citeste continutul UTF-8 al unui fisier text.

        Exceptiile de tip FileNotFoundError sau PermissionError nu sunt mascate.
        Ele trebuie tratate de apelant, daca este necesar.
        """
        return path.read_text(encoding="utf-8")

    def write_text(self, path: Path, content: str) -> None:
        """
        Scrie continut UTF-8 intr-un fisier text.

        Directorul parinte este creat automat daca nu exista.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def read_lines(self, path: Path) -> list[str]:
        """
        Returneaza liniile unui fisier text, fara caracterele de newline finale.
        """
        return self.read_text(path).splitlines()

    def file_exists(self, path: Path) -> bool:
        """
        Verifica existenta unui fisier sau director.
        """
        return path.exists()

    def ensure_directory_exists(self, path: Path) -> None:
        """
        Creeaza un director daca nu exista deja.
        """
        path.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Operatii pe fisierele principale ale proiectului
    # ------------------------------------------------------------------

    def get_current_dir(self) -> Path:
        """
        Returneaza directorul curent al framework-ului.
        """
        return self.config.paths.current_dir

    def get_file_under_test_path(self) -> Path:
        """
        Returneaza calea catre fisierul care contine codul testat.
        """
        return self.config.paths.file_under_test

    def get_rules_file_path(self) -> Path:
        """
        Returneaza calea catre Rules.md.
        """
        return self.config.paths.rules_file

    def get_proposal_test_file_path(self) -> Path:
        """
        Returneaza calea catre test_propunere.py.
        """
        return self.config.paths.proposal_test_file

    def get_testing_md_files(self) -> list[Path]:
        """
        Returneaza toate fisierele testing_*.md din directorul curent, sortate.

        Aceasta metoda centralizeaza conventia de nume pentru fisierele
        de descriere a categoriilor de testare.
        """
        pattern = f"{self.config.test_rules.prefix_testing_md}*.md"
        files = sorted(self.get_current_dir().glob(pattern))
        return files

    def map_testing_md_to_test_py(self, testing_md_path: Path) -> Path:
        """
        Mapeaza un fisier de forma testing_<categorie>.md la test_<categorie>.py.

        Exemplu:
        - testing_structural.md -> test_structural.py
        """
        stem = testing_md_path.stem
        prefix = self.config.test_rules.prefix_testing_md

        if not stem.startswith(prefix):
            raise ValueError(
                f"Fisierul {testing_md_path.name} nu respecta prefixul {prefix}."
            )

        category = stem[len(prefix):]
        test_file_name = f"{self.config.test_rules.prefix_test_py}{category}.py"
        return self.get_current_dir() / test_file_name

    def get_category_name_from_testing_md(self, testing_md_path: Path) -> str:
        """
        Extrage numele categoriei dintr-un fisier testing_<categorie>.md.
        """
        stem = testing_md_path.stem
        prefix = self.config.test_rules.prefix_testing_md

        if not stem.startswith(prefix):
            raise ValueError(
                f"Fisierul {testing_md_path.name} nu respecta prefixul {prefix}."
            )

        return stem[len(prefix):]

    def build_testing_file_mapping(self) -> dict[str, str]:
        """
        Construieste maparea dintre fisierele testing_*.md si test_*.py.

        Cheia este numele fisierului markdown, iar valoarea este numele
        fisierului Python de test asociat.
        """
        mapping: dict[str, str] = {}

        for testing_md_file in self.get_testing_md_files():
            test_py_file = self.map_testing_md_to_test_py(testing_md_file)
            mapping[testing_md_file.name] = test_py_file.name

        return mapping

    # ------------------------------------------------------------------
    # Importuri standard si fisiere de test
    # ------------------------------------------------------------------

    def ensure_standard_test_imports(self, content: str) -> str:
        """
        Se asigura ca importurile standard pentru test files exista la inceput.

        Daca fisierul este gol, se returneaza doar importurile.
        Daca importurile exista deja exact in forma standard, continutul este
        returnat nemodificat.
        """
        standard_imports = self.config.test_rules.importuri_teste
        stripped_content = content.lstrip()

        if stripped_content.startswith(standard_imports):
            return stripped_content

        if not stripped_content:
            return standard_imports

        return standard_imports + "\n" + stripped_content

    def create_missing_test_files(self) -> dict[str, str]:
        """
        Creeaza fisierele test_*.py lipsa pentru toate fisierele testing_*.md.

        Fisierele create primesc importurile standard de test.
        Returneaza maparea dintre fisierele markdown si fisierele test Python.
        """
        mapping = self.build_testing_file_mapping()

        for testing_md_name, test_py_name in mapping.items():
            test_path = self.get_current_dir() / test_py_name

            if not test_path.exists():
                self.logger.debug(f"Se creeaza fisierul lipsa {test_py_name}.")
                self.write_text(
                    test_path,
                    self.config.test_rules.importuri_teste,
                )

        return mapping

    def ensure_test_file_initialized(self, test_file_path: Path) -> None:
        """
        Se asigura ca un fisier de test exista si contine macar importurile standard.
        """
        if not test_file_path.exists():
            self.write_text(
                test_file_path,
                self.config.test_rules.importuri_teste,
            )
            return

        current_content = self.read_text(test_file_path)
        normalized_content = self.ensure_standard_test_imports(current_content)

        if normalized_content != current_content:
            self.write_text(test_file_path, normalized_content)

    def get_runnable_test_files(self) -> list[str]:
        """
        Returneaza lista fisierelor test_*.py care contin cel putin o functie test_*.

        Aceste fisiere sunt cele care merita date mai departe catre pytest,
        coverage sau mutmut.
        """
        runnable_files: list[str] = []

        pattern = f"{self.config.test_rules.prefix_test_py}*.py"
        for test_file in sorted(self.get_current_dir().glob(pattern)):
            content = self.read_text(test_file).strip() if test_file.exists() else ""
            if "def test_" in content:
                runnable_files.append(test_file.name)

        return runnable_files

    # ------------------------------------------------------------------
    # Operatii pe fisierul temporar test_propunere.py
    # ------------------------------------------------------------------

    def clear_proposal_test_file(self) -> None:
        """
        Goleste fisierul temporar test_propunere.py si lasa doar importurile standard.
        """
        self.write_text(
            self.get_proposal_test_file_path(),
            self.config.test_rules.importuri_teste,
        )

    def overwrite_proposal_with_function(self, function_code: str) -> None:
        """
        Suprascrie test_propunere.py cu o singura functie propusa.

        Importurile standard sunt adaugate automat la inceput.
        """
        content = self.ensure_standard_test_imports(function_code.strip() + "\n")
        self.write_text(self.get_proposal_test_file_path(), content)

    # ------------------------------------------------------------------
    # Operatii pe functii si fisiere de test ale categoriilor
    # ------------------------------------------------------------------

    def function_exists_in_file(
        self,
        file_path: Path,
        function_name: str | None,
    ) -> bool:
        """
        Verifica daca o functie exista deja intr-un fisier de test.

        Daca numele functiei este None sau fisierul nu exista, se returneaza False.
        """
        if not function_name or not file_path.exists():
            return False

        content = self.read_text(file_path)
        pattern = rf"^def\s+{re.escape(function_name)}\s*\("
        return re.search(pattern, content, flags=re.MULTILINE) is not None

    def append_function_to_test_file(
        self,
        test_file_path: Path,
        function_code: str,
    ) -> None:
        """
        Adauga o functie noua intr-un fisier de test.

        Comportament:
        - pastreaza importurile standard la inceput
        - pastreaza comentariul care marcheaza sfarsitul testelor initiale,
          daca acesta exista deja
        - adauga functia noua inaintea acestui comentariu final
        """
        old_content = self.read_text(test_file_path) if test_file_path.exists() else ""
        old_content = self.ensure_standard_test_imports(old_content)

        final_initial_tests_comment = (
            self.config.test_rules.comentariu_final_teste_initiale
        )

        had_final_comment = final_initial_tests_comment in old_content
        content_without_final_comment = old_content.replace(
            final_initial_tests_comment,
            "",
        ).rstrip()

        new_content = content_without_final_comment
        if new_content:
            new_content += "\n\n"

        new_content += function_code.strip() + "\n"

        if had_final_comment:
            new_content = new_content.rstrip() + "\n\n"
            new_content += final_initial_tests_comment + "\n"

        self.write_text(test_file_path, new_content)

    def add_final_comment_to_initial_test_files(self) -> None:
        """
        Adauga in toate fisierele test_*.py comentariul care marcheaza
        finalul etapei de teste initiale.

        test_propunere.py este exclus, deoarece este doar un fisier temporar.
        """
        final_comment = self.config.test_rules.comentariu_final_teste_initiale
        proposal_file_name = self.get_proposal_test_file_path().name

        pattern = f"{self.config.test_rules.prefix_test_py}*.py"
        for test_file in self.get_current_dir().glob(pattern):
            if test_file.name == proposal_file_name:
                continue

            content = self.read_text(test_file) if test_file.exists() else ""
            content = self.ensure_standard_test_imports(content)

            if final_comment not in content:
                content = content.rstrip()
                if content:
                    content += "\n\n"
                content += final_comment + "\n"
                self.write_text(test_file, content)

    # ------------------------------------------------------------------
    # Validari de structura initiala a proiectului
    # ------------------------------------------------------------------

    def validate_initial_project_structure(self) -> None:
        """
        Verifica existenta si coerenta minima a fisierelor necesare proiectului.

        Verificari:
        - exista to_test.py
        - exista Rules.md
        - Rules.md contine cel putin doua headere care incep cu #
        - exista cel putin un fisier testing_*.md
        - exista directorul de arhiva
        - exista si este initializat test_propunere.py
        - exista sau sunt create fisierele test_*.py aferente categoriilor
        """
        file_under_test = self.get_file_under_test_path()
        if not file_under_test.exists():
            raise FileNotFoundError(
                "Nu exista fisierul to_test.py, continand functia / clasa de testat"
            )

        rules_file = self.get_rules_file_path()
        if not rules_file.exists():
            raise FileNotFoundError("Nu exista fisierul Rules.md.")

        rules_lines = self.read_lines(rules_file)
        headers_count = sum(1 for line in rules_lines if line.startswith("#"))
        if headers_count < 3:
            raise ValueError(
                "Fisierul Rules.md trebuie sa contina cel putin 3 randuri care incep cu #."
            )

        testing_md_files = self.get_testing_md_files()
        if not testing_md_files:
            raise FileNotFoundError(
                "Nu exista niciun fisier testing_*.md cu categorii de teste."
            )

        self.ensure_directory_exists(self.config.paths.archive_dir)
        self.create_missing_test_files()
        self.clear_proposal_test_file()


    # ------------------------------------------------------------------
    # Parsare de baza pentru fisiere markdown
    # ------------------------------------------------------------------

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
            if re.match(r"^\d+\.", lines[index].strip()):
                end = index
                break

        return "\n".join(lines[start:end]).strip()


    def extract_testing_rule_bullets(self, markdown_path: Path) -> list[str]:
        """
        Extrage toate bullet-urile numerotate dintr-un fisier testing_*.md.

        Exemplu:
        - '1. test both true and false outcomes of decisions'
        """
        bullets: list[str] = []

        for line in self.read_lines(markdown_path):
            match = re.match(r"^\d+\.\s*(.+)$", line.strip())
            if match:
                bullets.append(match.group(1).strip())

        return bullets


    def count_testing_rule_bullets(self, markdown_path: Path) -> int:
        """
        Returneaza numarul bullet-urilor numerotate dintr-un fisier testing_*.md.
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
            if re.match(r"^\d+\.\s+.+$", line.strip())
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


    def append_extension_function_to_test_file(
        self,
        test_file_path: Path,
        function_code: str,
    ) -> None:
        """
        Adauga o functie noua de extensie (etapa 2) la finalul fisierului de test.

        Comportament:
        - pastreaza importurile standard la inceput
        - pastreaza comentariul care marcheaza sfarsitul testelor initiale,
        daca acesta exista deja
        - adauga functia noua dupa acest comentariu final, nu inaintea lui
        """
        old_content = self.read_text(test_file_path) if test_file_path.exists() else ""
        old_content = self.ensure_standard_test_imports(old_content)

        new_content = old_content.rstrip()
        if new_content:
            new_content += "\n\n"

        new_content += function_code.strip() + "\n"

        self.write_text(test_file_path, new_content)


    # ------------------------------------------------------------------
    # Utilitare pentru continutul codului sursa
    # ------------------------------------------------------------------

    def read_file_under_test_source(self) -> str:
        """
        Citeste continutul complet din to_test.py.
        """
        return self.read_text(self.get_file_under_test_path())


    def read_category_test_file_content(self, testing_md_path: Path) -> str:
        """
        Citeste continutul fisierului test_<categorie>.py asociat unei categorii.
        """
        test_file_path = self.map_testing_md_to_test_py(testing_md_path)
        self.ensure_test_file_initialized(test_file_path)
        return self.read_text(test_file_path)


    def read_rules_file_content(self) -> str:
        """
        Citeste continutul complet din Rules.md.
        """
        return self.read_text(self.get_rules_file_path())
    

