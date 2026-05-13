from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class LoggerFilesMixin:
    def _ensure_debug_directory_exists(self) -> None:
        """
        Creeaza directorul de loguri tehnice daca nu exista deja.
        """
        self.config.paths.debug_dir.mkdir(parents=True, exist_ok=True)

    def _append_text_line(self, file_path: Path, text: str) -> None:
        """
        Adauga o linie text la finalul unui fisier.

        Fisierul este creat automat daca nu exista.
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("a", encoding="utf-8") as file:
            file.write(text + "\n")

    def _read_jsonl_file(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Citeste un fisier JSON Lines si returneaza lista de obiecte JSON valide.

        Liniile goale sunt ignorate.
        Daca o linie este invalida JSON, ea este ignorata pentru robustete.
        """
        if not file_path.exists() or file_path.stat().st_size == 0:
            return []

        entries: list[dict[str, Any]] = []

        with file_path.open("r", encoding="utf-8") as file:
            for line in file:
                stripped_line = line.strip()
                if not stripped_line:
                    continue

                try:
                    parsed = json.loads(stripped_line)
                    if isinstance(parsed, dict):
                        entries.append(parsed)
                except json.JSONDecodeError:
                    # Se ignora liniile corupte pentru a nu bloca executia.
                    continue

        return entries

    def _current_timestamp(self) -> str:
        """
        Returneaza data si ora curenta intr-un format usor de citit.
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def debug(self, message: str) -> None:
        """
        Salveaza un mesaj tehnic de debug doar in fisierul de log, nu si in terminal.

        Diferenta fata de varianta veche:
        - daca mesajul are mai multe linii, fiecare linie este scrisa separat,
        cu timestamp si prefix propriu
        - astfel logul ramane lizibil si usor de urmarit
        """
        if not self.debugging_enabled:
            return

        lines = str(message).splitlines() or [""]
        for line in lines:
            formatted_message = f"[AutoTesting] {line}"
            timestamped_message = f"{self._current_timestamp()} {formatted_message}"
            self._append_text_line(
                self.config.paths.debug_log_file,
                timestamped_message,
            )

    def debug_block(self, title: str, content: str) -> None:
        """
        Scrie un bloc multi-line in logul de debug, cu un titlu clar.

        Este util pentru:
        - output-uri scurte de pytest
        - comparatii before/after
        - motive de respingere
        - prompturi sau raspunsuri sintetizate
        """
        if not self.debugging_enabled:
            return

        self.debug(f"{title}")
        if not (content or "").strip():
            self.debug("(gol)")
            return

        for line in content.splitlines():
            self.debug(f"    {line}")

    def log_validation_failure(
        self,
        category: str,
        validation_message: str,
        function_name: str | None = None,
    ) -> None:
        """
        Logheaza clar o validare esuata pentru o propunere AI.

        Scop:
        - sa vedem imediat in log pentru ce categorie a picat validarea
        - sa vedem, daca exista, numele functiei propuse
        - sa pastram mesajul concret de eroare care va fi trimis si la corectie
        """
        function_label = function_name or "functie_fara_nume"

        self.debug(
            f"[VALIDATION FAILED] categorie={category}; functie={function_label}"
        )
        self.debug_block(
            "Mesaj validare:",
            validation_message or "(fara mesaj de validare)",
        )

    def log_stage2_scores(
        self,
        category: str,
        before_scores_text: str,
        after_scores_text: str | None = None,
        selected_test_files: list[str] | None = None,
    ) -> None:
        """
        Logheaza scorurile folosite in etapa 2.

        before_scores_text si after_scores_text sunt deja formatate de
        TestsPerformance.format_scores_for_debug(...), pentru a evita logica
        redundanta in Logger.
        """
        selected_files_text = ", ".join(selected_test_files or []) or "nespecificat"

        self.debug(
            f"[STAGE2 SCORES] categorie={category}; fisiere={selected_files_text}"
        )
        self.debug(f"Scoruri before: {before_scores_text}")

        if after_scores_text is not None:
            self.debug(f"Scoruri after: {after_scores_text}")

    def log_stage2_decision(
        self,
        category: str,
        accepted: bool,
        reason: str,
        function_name: str | None = None,
        improvement: str | None = None,
    ) -> None:
        """
        Logheaza decizia finala pentru o propunere din etapa 2.

        accepted:
        - True  -> propunerea a fost acceptata
        - False -> propunerea a fost respinsa
        """
        decision = "ACCEPTED" if accepted else "REJECTED"
        function_label = function_name or "functie_fara_nume"

        self.debug(
            f"[STAGE2 {decision}] categorie={category}; functie={function_label}"
        )

        if improvement:
            self.debug(f"Imbunatatire: {improvement}")

        self.debug_block(
            "Motiv decizie:",
            reason or "(fara motiv explicit)",
        )

    def log_duplicate_or_repeated_proposal(
        self,
        category: str,
        function_name: str | None,
        reason: str,
    ) -> None:
        """
        Logheaza separat cazurile in care o propunere este ignorata deoarece:
        - functia exista deja in fisierul categoriei
        - hash-ul propunerii a mai fost respins anterior
        """
        function_label = function_name or "functie_fara_nume"

        self.debug(
            f"[STAGE2 DUPLICATE/REPEATED] categorie={category}; functie={function_label}"
        )
        self.debug_block("Motiv:", reason or "(fara motiv explicit)")

    def info(self, message: str) -> None:
        """
        Alias semantic pentru mesaje afisate in terminal.
        """
        self.console(message)

    def warning(self, message: str) -> None:
        """
        Afiseaza un mesaj de avertizare in terminal si, optional, il salveaza
        si in fisierul de debug.
        """
        formatted_message = f"[AutoTesting][WARNING] {message}"

        if self.print_debug:
            print(formatted_message)

        if self.debugging_enabled:
            timestamped_message = f"{self._current_timestamp()} {formatted_message}"
            self._append_text_line(
                self.config.paths.debug_log_file,
                timestamped_message,
            )

    def error(self, message: str) -> None:
        """
        Afiseaza un mesaj de eroare in terminal si, optional, il salveaza
        si in fisierul de debug.
        """
        formatted_message = f"[AutoTesting][ERROR] {message}"

        if self.print_debug:
            print(formatted_message)

        if self.debugging_enabled:
            timestamped_message = f"{self._current_timestamp()} {formatted_message}"
            self._append_text_line(
                self.config.paths.debug_log_file,
                timestamped_message,
            )

    def clear_debug_log(self) -> None:
        """
        Goleste fisierul de debug general.

        Este util mai ales in testare sau intre rulari separate ale framework-ului.
        """
        if self.config.paths.debug_log_file.exists():
            self.config.paths.debug_log_file.write_text("", encoding="utf-8")

    def clear_ollama_log(self) -> None:
        """
        Goleste fisierele de conversatii cu Ollama.
        """
        for log_file in (
            self.config.paths.ollama_log_file,
            self.config.paths.ollama_prompts_log_file,
            self.config.paths.ollama_responses_log_file,
        ):
            if log_file.exists():
                log_file.write_text("", encoding="utf-8")

    def log_exception(self, context: str, exception: Exception) -> None:
        """
        Metoda utilitara pentru logarea consistenta a exceptiilor.

        Nu arunca exceptia mai departe. Doar o descrie in logul tehnic.
        Tratarea efectiva a exceptiei ramane responsabilitatea apelantului.
        """
        self.error(f"{context}: {type(exception).__name__}: {exception}")
