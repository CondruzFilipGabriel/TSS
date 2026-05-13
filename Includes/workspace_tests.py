from __future__ import annotations
from pathlib import Path
import re


class WorkspaceTestsMixin:
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
