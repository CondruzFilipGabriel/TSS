from __future__ import annotations

"""
Archive.py

Rol
---
Acest fisier gestioneaza arhivarea artefactelor finale produse sau folosite
de framework-ul de generare automata de teste.

Scopul lui este sa scoata din orchestrator logica de:
- identificare a urmatorului folder de arhiva
- creare a folderului de arhiva
- mutare a fisierului to_test.py
- mutare a tuturor fisierelor test_*.py

Observatii
----------
1. Acest modul nu decide cand se face arhivarea. El doar executa arhivarea.
2. Acest modul nu se ocupa de logs. Logging-ul este delegat lui Logger.py.
3. Acest modul nu arhiveaza orice fisier din proiect, ci doar artefactele
   relevante pentru fluxul actual:
   - to_test.py
   - test_*.py
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from Config import AppConfig
from Logger import Logger
from WorkspaceManager import WorkspaceManager


@dataclass(frozen=True)
class ArchiveResult:
    """
    Reprezinta rezultatul unei operatii de arhivare.

    Campuri:
    - archive_folder: folderul de arhiva creat
    - moved_files: lista fisierelor mutate efectiv
    """

    archive_folder: Path
    moved_files: list[Path]


class ArchiveManager:
    """
    Gestioneaza arhivarea finala a artefactelor framework-ului.

    Parametri:
    - config: configurarea centrala a aplicatiei
    - logger: logger-ul folosit pentru debug si erori
    - workspace: managerul fisierelor proiectului
    """

    def __init__(
        self,
        config: AppConfig,
        logger: Logger,
        workspace: WorkspaceManager,
    ) -> None:
        self.config = config
        self.logger = logger
        self.workspace = workspace


    # ------------------------------------------------------------------
    # Helpers interni pentru folderul de arhiva
    # ------------------------------------------------------------------

    def ensure_archive_directory_exists(self) -> None:
        """
        Se asigura ca directorul principal de arhiva exista.
        """
        self.workspace.ensure_directory_exists(self.config.paths.archive_dir)


    def get_existing_archive_subfolders(self) -> list[Path]:
        """
        Returneaza toate subfolderele existente din directorul principal de arhiva.
        """
        self.ensure_archive_directory_exists()

        return [
            entry
            for entry in self.config.paths.archive_dir.iterdir()
            if entry.is_dir()
        ]


    def extract_archive_number(self, archive_subfolder: Path) -> int | None:
        """
        Incearca sa extraga numarul de ordine din numele unui subfolder de arhiva.

        Formatul asteptat este compatibil cu implementarea initiala:
        "<numar> <data>"

        Exemple:
        - "1 18.04.2026 15:30" -> 1
        - "12 01.01.2026 09:00" -> 12

        Daca numarul nu poate fi extras, se returneaza None.
        """
        try:
            first_token = archive_subfolder.name.split(" ", 1)[0]
            return int(first_token)
        except (ValueError, IndexError):
            return None


    def get_next_archive_number(self) -> int:
        """
        Calculeaza urmatorul numar de ordine pentru o arhiva noua.
        """
        existing_subfolders = self.get_existing_archive_subfolders()
        existing_numbers: list[int] = []

        for subfolder in existing_subfolders:
            extracted_number = self.extract_archive_number(subfolder)
            if extracted_number is not None:
                existing_numbers.append(extracted_number)

        return max(existing_numbers, default=0) + 1


    def build_archive_folder_name(self, archive_number: int) -> str:
        """
        Construieste numele folderului de arhiva in formatul folosit anterior:
        "<numar> <data_curenta>"
        """
        current_date = datetime.now().strftime("%d.%m.%Y %H:%M")
        return f"{archive_number} {current_date}"


    def create_new_archive_folder(self) -> Path:
        """
        Creeaza si returneaza un subfolder nou de arhiva.
        """
        self.ensure_archive_directory_exists()

        next_number = self.get_next_archive_number()
        folder_name = self.build_archive_folder_name(next_number)
        archive_folder = self.config.paths.archive_dir / folder_name
        archive_folder.mkdir(parents=True, exist_ok=False)

        self.logger.debug(f"A fost creat folderul de arhiva: {archive_folder.name}")
        return archive_folder


    # ------------------------------------------------------------------
    # Selectia fisierelor de arhivat
    # ------------------------------------------------------------------

    def get_file_under_test_if_exists(self) -> Path | None:
        """
        Returneaza calea catre to_test.py daca fisierul exista, altfel None.
        """
        file_under_test = self.config.paths.file_under_test
        if file_under_test.exists() and file_under_test.is_file():
            return file_under_test
        return None


    def get_test_files_to_archive(self) -> list[Path]:
        """
        Returneaza toate fisierele test_*.py care trebuie arhivate.

        Regula noua:
        - test_propunere.py este exclus, deoarece este doar un fisier temporar
        de lucru si nu reprezinta un artefact final al sesiunii
        - restul fisierelor test_*.py raman compatibile cu conventia actuala
        a proiectului
        """
        pattern = f"{self.config.test_rules.prefix_test_py}*.py"
        proposal_file_name = self.config.files.proposal_test_file_name

        return [
            test_file
            for test_file in sorted(self.config.paths.current_dir.glob(pattern))
            if test_file.is_file() and test_file.name != proposal_file_name
        ]
    

    def get_files_to_archive(self) -> list[Path]:
        """
        Construieste lista completa a fisierelor care trebuie arhivate.

        Ordinea este:
        1. to_test.py, daca exista
        2. toate fisierele finale test_*.py existente, cu excluderea lui
        test_propunere.py
        """
        files_to_archive: list[Path] = []

        file_under_test = self.get_file_under_test_if_exists()
        if file_under_test is not None:
            files_to_archive.append(file_under_test)

        files_to_archive.extend(self.get_test_files_to_archive())
        return files_to_archive


    # ------------------------------------------------------------------
    # Mutarea efectiva a fisierelor
    # ------------------------------------------------------------------

    def move_file_to_archive(
        self,
        source_file: Path,
        archive_folder: Path,
    ) -> Path:
        """
        Muta un fisier in folderul de arhiva si returneaza noua lui cale.
        """
        destination_file = archive_folder / source_file.name
        moved_file = source_file.rename(destination_file)

        self.logger.debug(
            f"Fisier arhivat: {source_file.name} -> {archive_folder.name}"
        )
        return moved_file


    # ------------------------------------------------------------------
    # Arhivare completa
    # ------------------------------------------------------------------

    def archive_current_session_artifacts(self) -> ArchiveResult:
        """
        Arhiveaza toate artefactele relevante ale sesiunii curente.

        Flux:
        - se creeaza un folder nou de arhiva
        - se identifica fisierele relevante
        - fiecare fisier este mutat in noul folder

        Returneaza:
        - calea folderului de arhiva creat
        - lista fisierelor mutate efectiv
        """
        archive_folder = self.create_new_archive_folder()
        files_to_archive = self.get_files_to_archive()
        moved_files: list[Path] = []

        for source_file in files_to_archive:
            moved_file = self.move_file_to_archive(
                source_file=source_file,
                archive_folder=archive_folder,
            )
            moved_files.append(moved_file)

        return ArchiveResult(
            archive_folder=archive_folder,
            moved_files=moved_files,
        )


    # ------------------------------------------------------------------
    # Utilitare de inspectie
    # ------------------------------------------------------------------

    def has_any_artifacts_to_archive(self) -> bool:
        """
        Verifica daca exista cel putin un artefact de arhivat.
        """
        return len(self.get_files_to_archive()) > 0
    

    def format_archive_result_for_debug(self, result: ArchiveResult) -> str:
        """
        Returneaza un text scurt, util pentru logging, cu rezultatul arhivarii.
        """
        moved_file_names = ", ".join(file_path.name for file_path in result.moved_files)

        if not moved_file_names:
            moved_file_names = "niciun fisier"

        return (
            f"Arhiva creata: {result.archive_folder.name}; "
            f"fisiere mutate: {moved_file_names}"
        )