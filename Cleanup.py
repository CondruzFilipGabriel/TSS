from __future__ import annotations

"""
Cleanup.py

Rol
---
Acest fisier gestioneaza curatenia tehnica a workspace-ului framework-ului
de generare automata de teste.

Scopul lui este sa elimine artefactele temporare sau reziduurile ramase dupa
rulari anterioare, astfel incat:
- fiecare rulare sa porneasca dintr-un mediu curat
- pytest, coverage si mutmut sa nu fie influentate de fisiere reziduale
- dupa terminarea executiei sa nu ramana fisiere temporare care pot strica
  urmatoarea rulare

De ce exista separat de Archive.py
----------------------------------
Archive.py are rolul de a pastra artefactele utile ale sesiunii:
- to_test.py
- test_*.py

Cleanup.py are rolul opus:
- sterge artefactele tehnice temporare
- reseteaza fisiere de lucru
- elimina directoare si cache-uri care pot incurca rularea ulterioara

Aceasta separare este mai curata si mai usor de intretinut.

Ce curata
---------
1. Artefacte mutmut:
   - mutants/
   - .mutmut-cache
   - __autotesting_pyproject_backup__.tmp
   
2. Artefacte pytest / coverage / Python:
   - .pytest_cache/
   - .coverage
   - toate directoarele __pycache__/ din proiect

3. Artefacte temporare ale framework-ului:
   - __validate_temp__.py
   - resetarea lui test_propunere.py

Observatii
----------
1. test_propunere.py nu este sters, ci resetat la continutul standard cu
   importurile de baza.
2. Logs.jsonl nu este sters.
3. Directorul arh/ nu este sters.
4. Curatarea este sigura: se sterg doar artefacte tehnice cunoscute.
"""

import shutil
from pathlib import Path

from Config import AppConfig
from Logger import Logger
from WorkspaceManager import WorkspaceManager


class CleanupManager:
    """
    Gestioneaza curatenia tehnica a proiectului inainte si dupa rulare.

    Parametri:
    - config: configurarea centrala a aplicatiei
    - logger: logger-ul folosit pentru mesaje de debug
    - workspace: managerul de fisiere al proiectului
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
    # Helpers interni
    # ------------------------------------------------------------------

    def _safe_remove_file(self, path: Path) -> None:
        """
        Sterge un fisier daca exista.

        Daca fisierul nu exista, nu se face nimic.
        """
        try:
            if path.exists() and path.is_file():
                path.unlink()
                self.logger.debug(f"A fost sters fisierul temporar: {path.name}")
        except OSError as error:
            self.logger.warning(
                f"Nu s-a putut sterge fisierul {path}: {type(error).__name__}: {error}"
            )

    def _safe_remove_directory(self, path: Path) -> None:
        """
        Sterge recursiv un director daca exista.

        Daca directorul nu exista, nu se face nimic.
        """
        try:
            if path.exists() and path.is_dir():
                shutil.rmtree(path)
                self.logger.debug(f"A fost sters directorul temporar: {path}")
        except OSError as error:
            self.logger.warning(
                f"Nu s-a putut sterge directorul {path}: {type(error).__name__}: {error}"
            )

    def _remove_all_pycache_directories(self) -> None:
        """
        Sterge recursiv toate directoarele __pycache__ din workspace.
        """
        current_dir = self.config.paths.current_dir

        for pycache_dir in current_dir.rglob("__pycache__"):
            self._safe_remove_directory(pycache_dir)


    def _cleanup_mutmut_artifacts(self) -> None:
        """
        Sterge artefactele specifice mutmut.
        """
        pyproject_backup_file = (
            self.config.paths.current_dir / "__autotesting_pyproject_backup__.tmp"
        )

        self._safe_remove_directory(self.config.paths.mutants_dir)
        self._safe_remove_directory(self.config.paths.mutmut_cache_path)
        self._safe_remove_file(pyproject_backup_file)


    def _cleanup_pytest_and_coverage_artifacts(self) -> None:
        """
        Sterge artefactele specifice pytest, coverage si Python runtime.
        """
        pytest_cache_dir = self.config.paths.current_dir / ".pytest_cache"
        coverage_file = self.config.paths.current_dir / ".coverage"

        self._safe_remove_directory(pytest_cache_dir)
        self._safe_remove_file(coverage_file)
        self._remove_all_pycache_directories()

    def _cleanup_framework_temp_artifacts(self) -> None:
        """
        Sterge sau reseteaza artefactele temporare folosite de framework.
        """
        self._safe_remove_file(self.config.paths.validate_temp_file)
        self.workspace.clear_proposal_test_file()

    def _cleanup_common_runtime_artifacts(self) -> None:
        """
        Executa tot setul comun de curatenie tehnica.
        """
        self._cleanup_mutmut_artifacts()
        self._cleanup_pytest_and_coverage_artifacts()
        self._cleanup_framework_temp_artifacts()

    # ------------------------------------------------------------------
    # Curatenie publica
    # ------------------------------------------------------------------

    def cleanup_before_run(self) -> None:
        """
        Executa curatenia de inceput de rulare.

        In terminal afisam un singur mesaj scurt si curat.
        Detaliile tehnice raman in logul de debug.
        """
        self.logger.console_step("curat workspace-ul de fisiere temporare")
        self._cleanup_common_runtime_artifacts()
        self.logger.debug("Curatenia initiala a workspace-ului s-a incheiat.")


    def cleanup_after_run(self) -> None:
        """
        Executa curatenia de final de rulare.

        In terminal afisam un singur mesaj scurt si curat.
        Detaliile tehnice raman in logul de debug.
        """
        self.logger.console_step("curat fisierele temporare")
        self._cleanup_common_runtime_artifacts()
        self.logger.debug("Curatenia finala a workspace-ului s-a incheiat.")