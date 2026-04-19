from __future__ import annotations

"""
Logger.py

Rol
---
Acest fisier centralizeaza toata logica de logging a framework-ului de
generare automata de teste.

Scopurile principale sunt:
- afisarea si salvarea mesajelor de debug ale executiei
- salvarea regulilor acceptate in fisierul Logs.jsonl
- citirea istoricului de reguli acceptate
- afisarea ultimelor reguli adaugate in sesiunea curenta
- salvarea interactiunilor brute cu Ollama, daca debugging-ul este activ

Observatii de utilizare
-----------------------
1. Clasa Logger poate afisa mesaje in terminal si, optional, le poate salva
   in fisierul de debug.

2. Clasa foloseste configurarea centralizata din Config.py:
   - pentru caile standard ale fisierelor
   - pentru directoarele de log
   - pentru numele fisierelor de debug si de istoric

3. Pentru compatibilitate cu fluxul existent, intrarile acceptate in
   Logs.jsonl sunt salvate in format JSON Lines, cate un obiect JSON pe linie.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from Config import AppConfig


class Logger:
    """
    Gestioneaza toate operatiile de logging ale framework-ului.

    Responsabilitati:
    - afisare mesaje de debug
    - scriere mesaje de debug in fisier
    - salvare reguli acceptate in Logs.jsonl
    - citire reguli salvate
    - afisare ultime reguli adaugate
    - salvare interactiuni brute cu Ollama

    Parametri:
    - config: obiectul central de configurare al aplicatiei
    - debugging_enabled: activeaza sau dezactiveaza logarea tehnica in fisiere
    - print_debug: controleaza daca mesajele de debug sunt afisate in terminal
    """

    def __init__(
        self,
        config: AppConfig,
        debugging_enabled: bool = False,
        print_debug: bool = True,
    ) -> None:
        self.config = config
        self.debugging_enabled = debugging_enabled
        self.print_debug = print_debug

        # Pregatim directoarele de log doar daca e necesar sa scriem efectiv
        # in fisiere de debug. Logs.jsonl poate exista si independent de ele.
        if self.debugging_enabled:
            self._ensure_debug_directory_exists()


    # ------------------------------------------------------------------
    # Helpers interne pentru directoare si fisiere
    # ------------------------------------------------------------------

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


    # ------------------------------------------------------------------
    # Debug logging
    # ------------------------------------------------------------------

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


    # ------------------------------------------------------------------
    # Logare reguli acceptate in Logs.jsonl
    # ------------------------------------------------------------------

    def _next_rule_entry_number(self) -> int:
        """
        Calculeaza urmatorul numar de intrare pentru Logs.jsonl.

        Daca fisierul nu exista sau este gol, numerotarea incepe de la 1.
        """
        entries = self._read_jsonl_file(self.config.paths.accepted_rules_log_file)
        if not entries:
            return 1

        last_entry = entries[-1]
        last_number = last_entry.get("Numar intrare", 0)

        if isinstance(last_number, int) and last_number >= 1:
            return last_number + 1

        return 1


    def append_rule(
        self,
        category: str,
        rule: str,
        reasoning: str,
        improvement: str,
        author: str = "AI",
    ) -> dict[str, Any]:
        """
        Adauga o intrare noua in Logs.jsonl pentru o regula acceptata.

        Campurile au fost pastrate compatibile cu structura folosita anterior
        in AutoTesting.py.
        """
        entry = {
            "Numar intrare": self._next_rule_entry_number(),
            "Categorie": category,
            "Regula": rule,
            "Motivare": reasoning,
            "Imbunatatire": improvement,
            "Data": self._current_timestamp(),
            "Autor": author,
        }

        self.config.paths.accepted_rules_log_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.config.paths.accepted_rules_log_file.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(json.dumps(entry, ensure_ascii=False) + "\n")

        if self.debugging_enabled:
            self._append_text_line(
                self.config.paths.debug_log_file,
                f"{self._current_timestamp()} [AutoTesting] Regula acceptata: "
                f"categorie={category}, regula={rule}",
            )

        return entry


    def read_all_rules(self) -> list[dict[str, Any]]:
        """
        Returneaza toate intrarile valide din Logs.jsonl.
        """
        return self._read_jsonl_file(self.config.paths.accepted_rules_log_file)


    def read_last_n_rules(self, count: int) -> list[dict[str, Any]]:
        """
        Returneaza ultimele `count` reguli din Logs.jsonl.

        Daca `count` este mai mic sau egal cu 0, se returneaza lista vida.
        """
        if count <= 0:
            return []

        all_rules = self.read_all_rules()
        if not all_rules:
            return []

        return all_rules[-count:]


    def print_last_added_rules(self, added_rules_count: int) -> None:
        """
        Afiseaza ultimele reguli adaugate in sesiunea curenta.

        Mesajele sunt trimise prin logger pentru a pastra acelasi stil in terminal
        si pentru a fi salvate si in fisierul de debug, daca acesta este activ.
        """
        if added_rules_count == 0:
            self.console(
                "Nu au fost identificate teste noi fata de tipurile deja existente in library-ul framework-ului de testare."
            )
            return

        last_entries = self.read_last_n_rules(added_rules_count)

        if not last_entries:
            self.console(f"Numar reguli adaugate: {added_rules_count}")
            self.console("Logs.jsonl nu exista sau este gol.")
            return

        self.console(f"Numar reguli adaugate: {added_rules_count}")
        for entry in last_entries:
            self.console(json.dumps(entry, ensure_ascii=False, indent=2))


    # ------------------------------------------------------------------
    # Logare interactiuni Ollama
    # ------------------------------------------------------------------

    def append_ollama_chat(
        self,
        prompt: str,
        response: str,
        model: str,
        duration_sec: float | None = None,
    ) -> None:
        """
        Salveaza o interactiune bruta cu Ollama.

        Aceasta metoda este activa doar daca debugging-ul este pornit.
        Formatul este JSON Lines pentru a permite inspectarea ulterioara
        si parsarea simpla.
        """
        if not self.debugging_enabled:
            return

        self._ensure_debug_directory_exists()

        payload: dict[str, Any] = {
            "timestamp": self._current_timestamp(),
            "model": model,
            "prompt": prompt,
            "response": response,
        }

        if duration_sec is not None:
            payload["duration_sec"] = round(duration_sec, 4)

        with self.config.paths.ollama_log_file.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False) + "\n")


    # ------------------------------------------------------------------
    # Utilitare generale pentru reset / inspectie
    # ------------------------------------------------------------------

    def clear_debug_log(self) -> None:
        """
        Goleste fisierul de debug general.

        Este util mai ales in testare sau intre rulari separate ale framework-ului.
        """
        if self.config.paths.debug_log_file.exists():
            self.config.paths.debug_log_file.write_text("", encoding="utf-8")


    def clear_ollama_log(self) -> None:
        """
        Goleste fisierul de conversatii cu Ollama.
        """
        if self.config.paths.ollama_log_file.exists():
            self.config.paths.ollama_log_file.write_text("", encoding="utf-8")


    def log_exception(self, context: str, exception: Exception) -> None:
        """
        Metoda utilitara pentru logarea consistenta a exceptiilor.

        Nu arunca exceptia mai departe. Doar o descrie in logul tehnic.
        Tratarea efectiva a exceptiei ramane responsabilitatea apelantului.
        """
        self.error(f"{context}: {type(exception).__name__}: {exception}")


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

    
    def separator(self) -> None:
        """
        Afiseaza un separator simplu in terminal si il salveaza in log.
        """
        self.console("-" * 60)