from __future__ import annotations
import json
from typing import Any



class LoggerConsoleMixin:
    def _append_jsonl_payload(self, file_path, payload: dict[str, Any]) -> None:
        """Scrie un obiect JSON pe o linie intr-un fisier JSONL."""
        self._ensure_debug_directory_exists()
        with file_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def append_ollama_chat(
        self,
        prompt: str,
        response: str,
        model: str,
        duration_sec: float | None = None,
    ) -> None:
        """
        Salveaza interactiunea completa cu Ollama in loguri persistente.

        Terminalul ramane scurt. Promptul complet si raspunsul brut sunt salvate
        in fisierele din logs/, ca sa poata fi analizate ulterior fara sa incarce
        outputul din consola.
        """
        timestamp = self._current_timestamp()
        duration_payload = {}
        if duration_sec is not None:
            duration_payload["duration_sec"] = round(duration_sec, 4)

        if self.config.logging.save_ollama_chat:
            self._append_jsonl_payload(
                self.config.paths.ollama_log_file,
                {
                    "timestamp": timestamp,
                    "model": model,
                    "prompt": prompt,
                    "response": response,
                    **duration_payload,
                },
            )

        if self.config.logging.save_ollama_prompts:
            self._append_jsonl_payload(
                self.config.paths.ollama_prompts_log_file,
                {
                    "timestamp": timestamp,
                    "model": model,
                    "prompt": prompt,
                    **duration_payload,
                },
            )

        if self.config.logging.save_ollama_responses:
            self._append_jsonl_payload(
                self.config.paths.ollama_responses_log_file,
                {
                    "timestamp": timestamp,
                    "model": model,
                    "response": response,
                    **duration_payload,
                },
            )

    def console(self, message: str) -> None:
        """
        Afiseaza un mesaj scurt in terminal si, optional, il salveaza si in
        fisierul de debug.

        Aceasta metoda este destinata mesajelor curate, orientate catre utilizator,
        nu detaliilor tehnice interne.
        """
        formatted_message = f"[AutoTesting] {message}"

        if self.print_debug:
            print(formatted_message)

        if self.debugging_enabled:
            timestamped_message = f"{self._current_timestamp()} {formatted_message}"
            self._append_text_line(
                self.config.paths.debug_log_file,
                timestamped_message,
            )

    def section(self, title: str) -> None:
        """
        Afiseaza un antet de etapa in terminal si il salveaza si in logul de debug.

        Exemplu:
        - Pregatiri initiale:
        - Etapa 1:
        - Etapa 2:
        - Final:
        """
        self.console(title)

    def console_step(self, message: str) -> None:
        """
        Afiseaza un mesaj de tip pas/bullet in terminal si il salveaza si in log.

        Exemplu:
        - curat workspace-ul de fisiere temporare
        - verific existenta conditiilor de rulare
        """
        self.console(f"    - {message}")

    def ai(self, message: str) -> None:
        """
        Afiseaza un mesaj scurt legat de AI in terminal, cu prefix clar 'AI:'.

        Aceasta metoda este pentru mesajele care trebuie sa ramana vizibile
        utilizatorului, dar formulate curat si unitar.
        """
        self.console(f"AI: {message}")

    def ai_debug(self, message: str) -> None:
        """
        Salveaza un mesaj tehnic legat de AI doar in fisierul de debug.

        Exemplu:
        - lungime prompt
        - preview prompt
        - lungime raspuns brut
        - preview output brut
        """
        self.debug(f"AI: {message}")

    def ai_technical(self, message: str) -> None:
        """Afiseaza mesaje tehnice AI doar daca sunt activate in config."""
        if self.config.terminal.show_ai_technical_messages:
            self.ai(message)
        else:
            self.ai_debug(message)

    def ollama_request_summary(self, summary: str) -> None:
        """Afiseaza in terminal doar rezumatul scurt al cererii catre Ollama."""
        self.console(f"Se trimite catre Ollama: {summary}")

    def ollama_prompt(self, prompt: str) -> None:
        """Afiseaza promptul trimis catre Ollama, daca setarea este activa."""
        if self.config.terminal.show_ollama_prompt:
            self.console("Se trimite catre Ollama:")
            print(prompt)
        self.debug_block("Prompt trimis catre Ollama:", prompt)

    def ollama_response(self, response: str) -> None:
        """Afiseaza raspunsul brut Ollama doar daca setarea este activa."""
        if self.config.terminal.show_ollama_response:
            self.console("Raspuns Ollama:")
            print(response or "(gol)")
        self.debug_block("Raspuns brut Ollama:", response or "(gol)")

    def separator(self) -> None:
        """
        Afiseaza un separator simplu in terminal si il salveaza in log.
        """
        self.console("-" * 60)
