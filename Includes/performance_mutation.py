from __future__ import annotations
import re
import shutil
import subprocess
from pathlib import Path


class PerformanceMutationMixin:
    def _prepare_mutmut_environment(self) -> bool:
        """
        Pregateste mediul pentru mutmut:
        - identifica daca pyproject.toml exista deja
        - curata cache-urile si directoarele temporare mutmut

        Returneaza:
        - had_pyproject: daca pyproject.toml exista inainte
        """
        pyproject_file = self._get_pyproject_file_path()
        pyproject_backup_file = self.config.paths.current_dir / "__autotesting_pyproject_backup__.tmp"

        mutmut_cache_path = self.config.paths.mutmut_cache_path
        mutants_dir = self.config.paths.mutants_dir

        had_pyproject = pyproject_file.exists()

        if had_pyproject:
            shutil.copy2(pyproject_file, pyproject_backup_file)

        if mutmut_cache_path.exists():
            if mutmut_cache_path.is_dir():
                shutil.rmtree(mutmut_cache_path)
            else:
                mutmut_cache_path.unlink()

        if mutants_dir.exists():
            if mutants_dir.is_dir():
                shutil.rmtree(mutants_dir)
            else:
                mutants_dir.unlink()

        return had_pyproject

    def _restore_mutmut_environment(self, had_pyproject: bool) -> None:
        """
        Restaureaza pyproject.toml dupa rularea mutmut.
        """
        pyproject_file = self._get_pyproject_file_path()
        pyproject_backup_file = self.config.paths.current_dir / "__autotesting_pyproject_backup__.tmp"

        if had_pyproject and pyproject_backup_file.exists():
            shutil.move(str(pyproject_backup_file), str(pyproject_file))
        elif pyproject_backup_file.exists():
            pyproject_backup_file.unlink(missing_ok=True)
            if pyproject_file.exists():
                pyproject_file.unlink()

    def run_mutation_score(
        self,
        selected_test_files: list[str] | None = None,
    ) -> float:
        """
        Ruleaza mutmut si returneaza procentul de mutanti eliminati pentru
        fisierele de test selectate.
        """
        test_files = self._get_runnable_test_files(selected_test_files)
        if not test_files:
            return 0.0

        self.logger.debug(f"Rulez testarea de mutatii pentru: {test_files}")

        pyproject_file = self._get_pyproject_file_path()
        had_pyproject = False

        try:
            had_pyproject = self._prepare_mutmut_environment()

            pyproject_text = self._build_mutmut_pyproject_text(test_files)
            self.workspace.write_text(pyproject_file, pyproject_text)

            run_result = self._run_command(
                command=["mutmut", "run"],
                timeout=self.config.timeouts.timeout_sec_mutmut,
            )
            run_output = self._combine_process_output(run_result)

            if self.logger.debugging_enabled:
                self.logger.debug("Output mutmut run:")
                for line in run_output.splitlines():
                    self.logger.debug(line)

            if (
                run_result.returncode != 0
                or "BadTestExecutionCommandsException" in run_output
                or "Failed to run pytest with args:" in run_output
                or "failed to collect stats" in run_output.lower()
            ):
                self.logger.warning(
                    "mutmut nu a putut rula pytest corect. Scorul de mutatie este setat la 0.0."
                )
                return 0.0

            if "no tests ran" in run_output.lower():
                return 0.0

            results_result = self._run_command(
                command=["mutmut", "results"],
                timeout=self.config.timeouts.timeout_sec,
            )
            results_output = self._combine_process_output(results_result)

            if self.logger.debugging_enabled:
                self.logger.debug("Output mutmut results:")
                for line in results_output.splitlines():
                    self.logger.debug(line)

            counts = {
                "survived": 0,
                "timeout": 0,
                "suspicious": 0,
                "skipped": 0,
                "not_checked": 0,
            }

            for raw_line in results_output.splitlines():
                line = raw_line.strip().lower()
                if not line or ":" not in line:
                    continue

                if line.endswith(": survived"):
                    counts["survived"] += 1
                elif line.endswith(": timeout"):
                    counts["timeout"] += 1
                elif line.endswith(": suspicious"):
                    counts["suspicious"] += 1
                elif line.endswith(": skipped"):
                    counts["skipped"] += 1
                elif line.endswith(": not checked"):
                    counts["not_checked"] += 1

            total_mutants = None
            run_lines = [line.strip() for line in run_output.splitlines() if line.strip()]

            for line in reversed(run_lines):
                match_total = re.search(r"(\d+)\s*/\s*(\d+)", line)
                if match_total:
                    left = int(match_total.group(1))
                    right = int(match_total.group(2))
                    if right > 0 and left == right:
                        total_mutants = right
                        break

            if total_mutants is None:
                self.logger.warning(
                    "Nu s-a putut extrage numarul total de mutanti din outputul mutmut run. Scorul de mutatie este setat la 0.0."
                )
                return 0.0

            unresolved_total = (
                counts["survived"]
                + counts["timeout"]
                + counts["suspicious"]
                + counts["skipped"]
                + counts["not_checked"]
            )

            if unresolved_total > total_mutants:
                self.logger.warning(
                    "Numarul de stari raportate de mutmut depaseste totalul mutantilor. Scorul de mutatie este setat la 0.0."
                )
                return 0.0

            killed = total_mutants - unresolved_total
            return round(killed * 100 / total_mutants, 2)

        except subprocess.TimeoutExpired:
            self.logger.warning(
                "mutmut a depasit timpul maxim de executie. Scorul de mutatie este setat la 0.0."
            )
            return 0.0
        except FileNotFoundError:
            self.logger.warning(
                "Executabilul mutmut nu a fost gasit. Scorul de mutatie este setat la 0.0."
            )
            return 0.0
        finally:
            self._restore_mutmut_environment(had_pyproject)
