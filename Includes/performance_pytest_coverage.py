from __future__ import annotations
import re
from pathlib import Path


class PerformancePytestCoverageMixin:
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
