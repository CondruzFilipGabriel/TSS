from __future__ import annotations
from pathlib import Path


class WorkspaceIOMixin:
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
