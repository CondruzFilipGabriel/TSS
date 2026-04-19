from __future__ import annotations

"""
TestsPerformance.py

Rol
---
Acest fisier evalueaza performanta suitei curente de teste, folosind toolurile
externe deja folosite in proiect:
- pytest
- coverage cu branch coverage
- mutmut

Scopul lui este sa scoata din orchestrator logica de masurare si comparare a
calitatii suitei de teste, astfel incat:
- AutoTesting.py sa ramana concentrat pe flux
- rularea toolurilor externe sa fie centralizata
- regulile de comparatie a scorurilor sa fie definite intr-un singur loc

Ce masoara
----------
1. Scor pytest:
   - scorul de stare al suitei la pytest: 100.0 daca suita este curata, altfel 
   un procent orientativ calculat din rezultatele relevante ale rularii

2. Scor coverage:
   - procentul de branch coverage pentru fisierul testat, to_test.py

3. Scor mutmut:
   - procentul de mutanti eliminati sau neutralizati prin timeout
   - formula folosita ramane compatibila cu implementarea existenta

4. Comparatie intre doua seturi de scoruri:
   - detectarea existentei unei imbunatatiri
   - formatarea mesajului de imbunatatire pentru log

De ce exista acest modul separat
--------------------------------
In varianta initiala, AutoTesting.py se ocupa direct de:
- rularea pytest
- rularea coverage
- rularea mutmut
- parsarea outputului acestor tooluri
- calcularea scorurilor curente
- compararea scorurilor inainte / dupa

Aceasta este o responsabilitate distincta si merita izolata pentru:
- claritate
- reutilizare
- testare separata
- reducerea cuplarii dintre fluxul principal si infrastructura externa

Observatii importante
---------------------
1. Acest modul nu valideaza testul propus. Asta este responsabilitatea
   lui TestValidator.py.

2. Acest modul nu decide acceptarea finala a unui test. El doar furnizeaza
   scorurile si verdictul de imbunatatire.

3. Lista fisierelor de test rulate este obtinuta din WorkspaceManager, pentru
   a pastra un singur punct de adevar privind ce fisiere sunt efectiv rulabile.
"""

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from Config import AppConfig
from Logger import Logger
from WorkspaceManager import WorkspaceManager


@dataclass(frozen=True)
class PerformanceScores:
    """
    Reprezinta cele trei scoruri principale folosite de framework.

    Campuri:
    - pytest_score: scorul de stare al suitei la pytest; 100.0 inseamna suita 
    curata, iar alte valori descriu o rulare necurata
    - coverage_score: procentul de branch coverage pentru to_test.py
    - mutation_score: procentul de mutanti eliminati
    """

    pytest_score: float
    coverage_score: float
    mutation_score: float


class TestsPerformance:
    """
    Evalueaza performanta suitei curente de teste.

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
    # Helpers generali
    # ------------------------------------------------------------------

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
    

    # ------------------------------------------------------------------
    # Pytest score
    # ------------------------------------------------------------------

    def run_pytest_score(
        self,
        selected_test_files: list[str] | None = None,
    ) -> float:
        """
        Ruleaza pytest pe fisierele de test selectate si returneaza
        un scor procentual orientat pe starea reala a suitei.

        Regula noua:
        - daca pytest se termina cu return code 0, consideram suita curata
        si returnam 100.0
        - skip-urile sau xfail-urile nu transforma singure suita intr-una "murdara"
        - daca exista esecuri reale, calculam procentul pe baza rezultatelor
        relevante pentru verdictul de executie
        """
        test_files = self._get_runnable_test_files(selected_test_files)
        if not test_files:
            return 0.0

        self.logger.debug(f"Rulez pytest pentru: {test_files}")

        command = ["python3", "-m", "pytest", "-q", *test_files]
        result = self._run_command(
            command=command,
            timeout=self.config.timeouts.timeout_sec,
        )
        output = self._combine_process_output(result)

        if "no tests ran" in output.lower():
            return 0.0

        if result.returncode == 0:
            return 100.0

        summary_line = None
        for line in reversed(output.splitlines()):
            if any(
                keyword in line
                for keyword in [
                    "passed",
                    "failed",
                    "error",
                    "errors",
                    "xpassed",
                ]
            ):
                summary_line = line.strip()
                break

        if summary_line is None:
            return 0.0

        counts = {
            "passed": 0,
            "failed": 0,
            "error": 0,
            "errors": 0,
            "xpassed": 0,
        }

        for key in counts:
            match = re.search(rf"(\d+)\s+{key}\b", summary_line)
            if match:
                counts[key] = int(match.group(1))

        total_relevant = sum(counts.values())
        if total_relevant == 0:
            return 0.0

        return round(counts["passed"] * 100 / total_relevant, 2)


    # ------------------------------------------------------------------
    # Coverage score
    # ------------------------------------------------------------------

    def run_branch_coverage_score(
        self,
        selected_test_files: list[str] | None = None,
    ) -> float:
        """
        Ruleaza coverage cu branch measurement pentru to_test.py si returneaza
        procentul de coverage pentru fisierele de test selectate.

        Regula noua:
        - daca rularea pytest sub coverage esueaza, scorul de coverage devine 0.0
        - nu folosim rapoarte partiale provenite din executii esuate
        """
        test_files = self._get_runnable_test_files(selected_test_files)
        if not test_files:
            return 0.0

        self.logger.debug(f"Rulez branch coverage pentru: {test_files}")

        self._run_command(
            command=["python3", "-m", "coverage", "erase"],
            timeout=self.config.timeouts.timeout_sec,
        )

        coverage_run_result = self._run_command(
            command=[
                "python3",
                "-m",
                "coverage",
                "run",
                "--branch",
                "-m",
                "pytest",
                "-q",
                *test_files,
            ],
            timeout=self.config.timeouts.timeout_sec,
        )

        coverage_run_output = self._combine_process_output(coverage_run_result)

        if coverage_run_result.returncode != 0:
            self.logger.debug(
                "Branch coverage este setat la 0.0 deoarece pytest sub coverage nu a rulat curat."
            )
            if self.logger.debugging_enabled:
                for line in coverage_run_output.splitlines():
                    self.logger.debug(line)
            return 0.0

        report_result = self._run_command(
            command=[
                "python3",
                "-m",
                "coverage",
                "report",
                "-m",
                f"--include={self.config.files.file_under_test_name}",
            ],
            timeout=self.config.timeouts.timeout_sec,
        )
        output = self._combine_process_output(report_result)

        if report_result.returncode != 0 or "No data to report" in output:
            return 0.0

        total_line = None
        for line in output.splitlines():
            stripped_line = line.strip()
            if stripped_line.startswith("TOTAL"):
                total_line = stripped_line
                break

        if total_line is None:
            for line in output.splitlines():
                stripped_line = line.strip()
                if stripped_line.startswith(self.config.files.file_under_test_name):
                    total_line = stripped_line
                    break

        if total_line is None:
            return 0.0

        match = re.search(r"(\d+%)\s*$", total_line)
        if match is None:
            return 0.0

        return float(match.group(1).replace("%", ""))


    # ------------------------------------------------------------------
    # Mutmut score
    # ------------------------------------------------------------------

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


    # ------------------------------------------------------------------
    # Scoruri agregate
    # ------------------------------------------------------------------

    def get_current_scores(
        self,
        selected_test_files: list[str] | None = None,
    ) -> PerformanceScores:
        """
        Returneaza setul curent de scoruri pentru fisierele de test selectate.

        Regula noua:
        - calculam intai pytest
        - daca pytest nu este curat, nu mai rulam coverage si mutmut
        - astfel evitam costuri mari pentru propuneri care oricum nu pot fi acceptate
        """
        pytest_score = self.run_pytest_score(selected_test_files)

        if pytest_score <= 0.0:
            return PerformanceScores(
                pytest_score=pytest_score,
                coverage_score=0.0,
                mutation_score=0.0,
            )

        if pytest_score < 100.0:
            return PerformanceScores(
                pytest_score=pytest_score,
                coverage_score=0.0,
                mutation_score=0.0,
            )

        return PerformanceScores(
            pytest_score=pytest_score,
            coverage_score=self.run_branch_coverage_score(selected_test_files),
            mutation_score=self.run_mutation_score(selected_test_files),
        )


    def get_current_scores_tuple(self) -> tuple[float, float, float]:
        """
        Metoda de compatibilitate cu stilul vechi din AutoTesting.py.
        """
        scores = self.get_current_scores()
        return (
            scores.pytest_score,
            scores.coverage_score,
            scores.mutation_score,
        )


    # ------------------------------------------------------------------
    # Compararea scorurilor
    # ------------------------------------------------------------------

    def has_improvement(
        self,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
    ) -> bool:
        """
        Returneaza True daca exista cel putin o imbunatatire intre cele doua
        seturi de scoruri.
        """
        return any(
            after > before
            for before, after in zip(
                (
                    before_scores.pytest_score,
                    before_scores.coverage_score,
                    before_scores.mutation_score,
                ),
                (
                    after_scores.pytest_score,
                    after_scores.coverage_score,
                    after_scores.mutation_score,
                ),
            )
        )


    def has_non_regressive_improvement(
        self,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
    ) -> bool:
        """
        Returneaza True doar daca:
        - niciun scor nu scade
        - cel putin un scor creste

        Asta previne acceptarea unor teste care cresc un scor,
        dar deterioreaza altul.
        """
        before_values = (
            before_scores.pytest_score,
            before_scores.coverage_score,
            before_scores.mutation_score,
        )
        after_values = (
            after_scores.pytest_score,
            after_scores.coverage_score,
            after_scores.mutation_score,
        )

        has_any_decrease = any(after < before for before, after in zip(before_values, after_values))
        has_any_increase = any(after > before for before, after in zip(before_values, after_values))

        return (not has_any_decrease) and has_any_increase


    def is_pytest_clean(self, scores: PerformanceScores) -> bool:
        """
        Returneaza True doar daca suita curenta nu are teste picate la pytest.

        In modelul actual, asta inseamna pytest_score >= 100.0.
        """
        return scores.pytest_score >= 100.0
    

    def has_strict_improvement(
        self,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
    ) -> bool:
        """
        Returneaza True doar daca:
        - suita era curata inainte (pytest 100%)
        - suita ramane curata dupa (pytest 100%)
        - niciun scor nu scade
        - cel putin un scor creste

        Aceasta regula previne acceptarea unor teste care par sa imbunatateasca
        anumite scoruri, dar introduc teste gresite logic si strica suita.
        """
        if not self.is_pytest_clean(before_scores):
            return False

        if not self.is_pytest_clean(after_scores):
            return False

        before_values = (
            before_scores.pytest_score,
            before_scores.coverage_score,
            before_scores.mutation_score,
        )
        after_values = (
            after_scores.pytest_score,
            after_scores.coverage_score,
            after_scores.mutation_score,
        )

        has_any_decrease = any(
            after < before for before, after in zip(before_values, after_values)
        )
        has_any_increase = any(
            after > before for before, after in zip(before_values, after_values)
        )

        return (not has_any_decrease) and has_any_increase


    def has_improvement_from_tuples(
        self,
        before_scores: tuple[float, float, float],
        after_scores: tuple[float, float, float],
    ) -> bool:
        """
        Metoda de compatibilitate pentru cod care lucreaza inca pe tuple.
        """
        return any(after > before for before, after in zip(before_scores, after_scores))


    def format_improvement(
        self,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
    ) -> str:
        """
        Formateaza textual imbunatatirea dintre doua seturi de scoruri, in stil
        compatibil cu logica existenta a framework-ului.
        """
        return (
            f"Pytest: {before_scores.pytest_score}% -> {after_scores.pytest_score}%; "
            f"Branch coverage: {before_scores.coverage_score}% -> {after_scores.coverage_score}%; "
            f"Mutmut: {before_scores.mutation_score}% -> {after_scores.mutation_score}%."
        )


    def format_improvement_from_tuples(
        self,
        before_scores: tuple[float, float, float],
        after_scores: tuple[float, float, float],
    ) -> str:
        """
        Metoda de compatibilitate pentru cod care lucreaza inca pe tuple.
        """
        pytest_before, coverage_before, mutation_before = before_scores
        pytest_after, coverage_after, mutation_after = after_scores

        return (
            f"Pytest: {pytest_before}% -> {pytest_after}%; "
            f"Branch coverage: {coverage_before}% -> {coverage_after}%; "
            f"Mutmut: {mutation_before}% -> {mutation_after}%."
        )

    # ------------------------------------------------------------------
    # Utilitare de prezentare
    # ------------------------------------------------------------------

    def format_scores_for_debug(self, scores: PerformanceScores) -> str:
        """
        Returneaza un text scurt pentru afisarea scorurilor curente in debug.
        """
        return (
            f"pytest: {scores.pytest_score}%, "
            f"coverage: {scores.coverage_score}%, "
            f"mutmut: {scores.mutation_score}%"
        )
    
    
    def explain_rejection_reason(
        self,
        before_scores: PerformanceScores,
        after_scores: PerformanceScores,
    ) -> str:
        """
        Returneaza un mesaj scurt care explica de ce o propunere nu trece
        criteriul strict de acceptare.
        """
        if not self.is_pytest_clean(before_scores):
            return (
                "Suita curenta nu este complet valida la pytest, deci nu se poate "
                "folosi criteriul strict de acceptare pana nu sunt eliminate testele gresite existente."
            )

        if not self.is_pytest_clean(after_scores):
            return (
                "Propunerea este respinsa deoarece dupa adaugare suita nu mai este curata la pytest."
            )

        before_values = (
            before_scores.pytest_score,
            before_scores.coverage_score,
            before_scores.mutation_score,
        )
        after_values = (
            after_scores.pytest_score,
            after_scores.coverage_score,
            after_scores.mutation_score,
        )

        has_any_decrease = any(
            after < before for before, after in zip(before_values, after_values)
        )
        has_any_increase = any(
            after > before for before, after in zip(before_values, after_values)
        )

        if has_any_decrease:
            return (
                "Propunerea este respinsa deoarece scade cel putin un scor."
            )

        if not has_any_increase:
            return (
                "Propunerea este respinsa deoarece nu imbunatateste niciun scor."
            )

        return "Propunerea poate fi acceptata."
    

    def has_any_tests(
        self,
        selected_test_files: list[str] | None = None,
    ) -> bool:
        """
        Returneaza True daca exista cel putin un fisier selectat care contine
        cel putin o functie de test rulabila.
        """
        test_files = self._get_runnable_test_files(selected_test_files)
        return len(test_files) > 0