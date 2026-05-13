from __future__ import annotations
import re
import subprocess


class ValidatorRuntimeMixin:
    def _build_validation_file_content(self, function_code: str) -> str:
        """
        Construieste continutul fisierului temporar folosit pentru validare.

        Se adauga importurile standard, apoi functia curatata.
        """
        imports = self.config.test_rules.importuri_teste
        return imports.rstrip() + "\n\n" + function_code.strip() + "\n"

    def _run_pytest_for_single_function(self, function_code: str) -> str:
        """
        Ruleaza pytest pentru functia propusa, intr-un fisier temporar.

        Regula:
        - return code 0 = testul trece -> valid
        - orice alt return code = invalid

        Diferenta fata de varianta veche:
        - mesajul de eroare este comprimat si curatat pentru a fi mai util
        in promptul de corectie
        """
        function_name = self.response_parser.extract_function_name(function_code)
        validation_temp_file = self.config.paths.validate_temp_file

        if not function_name:
            return (
                "The provided text does not contain any test function "
                "whose name starts with test_."
            )

        try:
            file_content = self._build_validation_file_content(function_code)
            self.workspace.write_text(validation_temp_file, file_content)

            command = [
                "python3",
                "-m",
                "pytest",
                "-q",
                f"{validation_temp_file.name}::{function_name}",
                "--maxfail=1",
            ]

            result = subprocess.run(
                command,
                cwd=self.config.paths.current_dir,
                capture_output=True,
                text=True,
                timeout=self.config.timeouts.timeout_sec,
            )

            output = (result.stdout or "") + (result.stderr or "")

            if result.returncode == 0:
                return "Valid"

            return self._extract_pytest_validation_message(
                pytest_output=output,
                function_name=function_name,
            )

        except subprocess.TimeoutExpired:
            return (
                f"TimeoutError: the test did not finish within "
                f"{self.config.timeouts.timeout_sec} seconds."
            )
        finally:
            if validation_temp_file.exists():
                validation_temp_file.unlink()

    def _extract_first_nonempty_lines(
        self,
        text: str,
        max_lines: int = 12,
    ) -> str:
        """
        Extrage primele linii utile dintr-un text lung, eliminand liniile goale.

        Este util pentru a reduce outputul brut din pytest la un mesaj mai scurt,
        usor de folosit in promptul de corectie.
        """
        useful_lines = [
            line.rstrip()
            for line in (text or "").splitlines()
            if line.strip()
        ]

        if not useful_lines:
            return ""

        return "\n".join(useful_lines[:max_lines]).strip()

    def _extract_pytest_validation_message(
        self,
        pytest_output: str,
        function_name: str,
    ) -> str:
        """
        Construieste un mesaj scurt si clar din outputul brut al pytest-ului.

        Prioritati:
        - erori de import / colectare
        - exceptii frecvente din rulare
        - assert failure
        - fallback la un excerpt scurt din output

        Scop:
        - mesajul trebuie sa fie suficient de concret pentru ca modelul sa poata
        corecta testul, fara sa primeasca un dump prea mare si zgomotos.
        """
        output = (pytest_output or "").strip()
        if not output:
            return "Pytest validation failed with no output."

        important_patterns = [
            r"(ImportError:.*)",
            r"(ModuleNotFoundError:.*)",
            r"(SyntaxError:.*)",
            r"(IndentationError:.*)",
            r"(NameError:.*)",
            r"(TypeError:.*)",
            r"(ValueError:.*)",
            r"(AttributeError:.*)",
            r"(KeyError:.*)",
            r"(IndexError:.*)",
            r"(AssertionError:.*)",
            r"(Failed:.*)",
        ]

        for pattern in important_patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1).strip()

        if "found no collectors" in output.lower():
            return (
                f"Pytest could not collect the generated test function {function_name}. "
                "Make sure the response contains exactly one valid test_* function."
            )

        excerpt = self._extract_first_nonempty_lines(output, max_lines=12)
        if excerpt:
            return excerpt

        return "Pytest validation failed."
