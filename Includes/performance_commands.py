from __future__ import annotations
import subprocess
import shutil
from pathlib import Path


class PerformanceCommandsMixin:
    def _run_command(
        self,
        command: list[str],
        timeout: int,
    ) -> subprocess.CompletedProcess[str]:
        """
        Ruleaza o comanda externa in directorul curent al proiectului.

        Stdout si stderr sunt capturate pentru a permite parsarea ulterioara.
        """
        return subprocess.run(
            command,
            cwd=self.config.paths.current_dir,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def _get_runnable_test_files(
        self,
        selected_test_files: list[str] | None = None,
    ) -> list[str]:
        """
        Returneaza lista fisierelor test_*.py care contin cel putin un test.

        Daca selected_test_files este furnizat, se filtreaza doar acele fisiere.
        """
        runnable_files = self.workspace.get_runnable_test_files()

        if selected_test_files is None:
            return runnable_files

        selected_set = {file_name for file_name in selected_test_files}
        return [file_name for file_name in runnable_files if file_name in selected_set]

    def _combine_process_output(
        self,
        result: subprocess.CompletedProcess[str],
    ) -> str:
        """
        Concateneaza stdout si stderr intr-un singur text.
        """
        return (result.stdout or "") + (result.stderr or "")

    def _get_pyproject_file_path(self) -> Path:
        """
        Returneaza calea catre pyproject.toml din directorul curent al proiectului.
        """
        return self.config.paths.current_dir / "pyproject.toml"

    def _build_mutmut_pyproject_text(self, test_files: list[str]) -> str:
        """
        Construieste continutul complet pentru pyproject.toml, controlat de framework,
        astfel incat mutmut sa primeasca explicit fisierele concrete de test.

        Se rescrie doar sectiunea tool.mutmut, deoarece pentru rularea automata
        a framework-ului aceasta este partea relevanta.
        """
        if not test_files:
            raise ValueError("Nu exista fisiere de test rulabile pentru mutmut.")

        quoted_test_files = ", ".join(f'"{file_name}"' for file_name in test_files)

        return (
            "[tool.mutmut]\n"
            f'paths_to_mutate = ["{self.config.files.file_under_test_name}"]\n'
            f"pytest_add_cli_args_test_selection = [{quoted_test_files}]\n"
            'pytest_add_cli_args = ["-q"]\n'
            "debug = true\n"
        )
