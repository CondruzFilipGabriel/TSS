from __future__ import annotations
import json
from datetime import datetime


class LoggerRulesMixin:
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
