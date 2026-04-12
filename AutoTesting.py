from pathlib import Path
import json
from datetime import datetime
import subprocess
import os
import select
import time
import ast
import re


class AutoTesting:
    """
    Clasa-orchestrator pentru generarea, validarea si selectiea automata
    a testelor pytest pentru fisierul to_test.py.

    Flux general:
    1. Verifica fisierele si structura minima necesara.
    2. Creeaza fisierele test_*.py corespunzatoare categoriilor testing_*.md.
    3. Porneste Aider + Ollama si scrie testele initiale deja enumerate in
       fisierele testing_*.md.
    4. Ruleaza o etapa de cautare a unor teste noi care imbunatatesc macar
       unul dintre scorurile:
           - pytest
           - branch coverage
           - cosmic-ray
    5. Logheaza regulile noi pastrate.
    6. Afiseaza regulile adaugate in sesiunea curenta.

    Principiul de selectie este strict:
    un test nou este pastrat doar daca imbunatateste cel putin un scor fata
    de starea existenta a suitei de teste.
    """

    COMENTARIU_FINAL_TESTE_INITIALE = (
        "# Sfarsitul implementarii testelor initiale existente."
    )

    def __init__(self):
        # Calea absoluta catre acest fisier si folderul curent de lucru.
        self.auto_testing_path = Path(__file__).resolve()
        self.folder_curent = self.auto_testing_path.parent

        # Mapare: nume fisier testing_*.md -> nume fisier test_*.py.
        self.fisiere_testing = {}

        # Lista ordonata a fisierelor testing_*.md.
        self.fisiere_testing_md = []

        # Timeout de referinta pentru interactiunea cu AI-ul.
        self.timeout_sec = 200

        # Numarul de reguli noi adaugate in sesiunea curenta.
        self.numar_reguli_adaugate = 0

        # Procesele externe controlate de clasa.
        self.aider_process = None
        self.ollama_process = None

        # Intreg fluxul este orchestrat direct din constructor.
        self.verifica_conditii_initiale()
        self.scrie_teste_initiale()
        self.gaseste_teste_noi()
        self.arhiveaza()
        self.afiseaza_reguli_adaugate()

    # -------------------------------------------------------------------------
    # Utilitare generale pentru fisiere si parsare de continut .md / text
    # -------------------------------------------------------------------------

    def _citeste_text(self, cale: Path) -> str:
        """Citeste un fisier text folosind UTF-8."""
        return cale.read_text(encoding="utf-8")

    def _scrie_text(self, cale: Path, continut: str):
        """Scrie un fisier text folosind UTF-8."""
        cale.write_text(continut, encoding="utf-8")

    def _linii(self, cale: Path) -> list[str]:
        """Intoarce liniile unui fisier text."""
        return self._citeste_text(cale).splitlines()

    def _fisiere_testing_md(self) -> list[Path]:
        """Intoarce toate fisierele testing_*.md din folderul curent."""
        return sorted(self.folder_curent.glob("testing_*.md"))

    def _fisier_test_pentru_md(self, fisier_md: Path) -> Path:
        """
        Construieste numele fisierului test_*.py asociat unui fisier
        testing_*.md.
        """
        categorie = fisier_md.stem[len("testing_"):]
        return self.folder_curent / f"test_{categorie}.py"

    def _pozitii_headere_principale(self, cale_md: Path) -> list[int]:
        """Intoarce pozitiile liniilor care incep cu '# '."""
        return [i for i, linie in enumerate(self._linii(cale_md)) if linie.startswith("# ")]

    def _extrage_sectiune_dupa_header(
        self,
        cale_md: Path,
        index_header: int,
        pana_la_urmatorul_header: bool = True,
    ) -> str:
        """
        Extrage textul de dupa headerul cu indexul dat.

        Exemplu:
        - index_header = 0 -> textul de dupa primul '# '
        - index_header = 1 -> textul de dupa al doilea '# '

        Daca pana_la_urmatorul_header este True, sectiunea se opreste la
        urmatorul '# '. Daca este False, merge pana la finalul fisierului.
        """
        linii = self._linii(cale_md)
        pozitii = self._pozitii_headere_principale(cale_md)

        if index_header >= len(pozitii):
            return ""

        start = pozitii[index_header] + 1
        end = len(linii)

        if pana_la_urmatorul_header and index_header + 1 < len(pozitii):
            end = pozitii[index_header + 1]

        return "\n".join(linii[start:end]).strip()

    def _extrage_reguli_generale_categorie(self, cale_md: Path) -> str:
        """
        Dintr-un fisier testing_*.md, extrage textul dintre primul '# ' si
        prima regula numerotata de forma '1.'.
        """
        linii = self._linii(cale_md)
        start = None
        end = len(linii)

        for i, linie in enumerate(linii):
            if linie.startswith("# "):
                start = i + 1
                break

        if start is None:
            return ""

        for i in range(start, len(linii)):
            if re.match(r"^\d+\.", linii[i].strip()):
                end = i
                break

        return "\n".join(linii[start:end]).strip()

    def _extrage_tipuri_teste(self, cale_md: Path) -> list[str]:
        """
        Extrage toate regulile numerotate dintr-un fisier testing_*.md.
        Intoarce doar textul de dupa numarul urmat de punct.
        """
        tipuri = []

        for linie in self._linii(cale_md):
            potrivire = re.match(r"^\d+\.\s*(.+)$", linie.strip())
            if potrivire:
                tipuri.append(potrivire.group(1).strip())

        return tipuri

    def _extrage_nume_functie_test(self, functie: str) -> str | None:
        """Extrage numele functiei test_* din codul primit ca text."""
        potrivire = re.search(r"def\s+(test_[A-Za-z0-9_]+)\s*\(", functie)
        if potrivire:
            return potrivire.group(1)
        return None

    def _extrage_regula_motivare(self, text: str) -> tuple[str, str]:
        """
        Extrage cele doua campuri cerute ulterior AI-ului:
        - Rule / Regula
        - Reasoning / Motivation / Motivare
        """
        linii = [linie.strip() for linie in text.splitlines() if linie.strip()]
        regula = ""
        motivare = ""

        prefixe_regula = ("rule:", "regula:")
        prefixe_motivare = ("reasoning:", "motivation:", "motivare:")

        for i, linie in enumerate(linii):
            lower = linie.lower()

            if lower.startswith(prefixe_regula):
                regula = linie.split(":", 1)[1].strip()
                continue

            if lower.startswith(prefixe_motivare):
                motivare = linie.split(":", 1)[1].strip()

                rest = [
                    x for x in linii[i + 1:]
                    if not x.lower().startswith(prefixe_regula + prefixe_motivare)
                ]
                if rest:
                    motivare = (motivare + "\n" + "\n".join(rest)).strip()
                break

        if not regula and linii:
            regula = linii[0]

        if not motivare and len(linii) > 1:
            motivare = "\n".join(linii[1:]).strip()

        return regula, motivare

    # -------------------------------------------------------------------------
    # Utilitare pentru editarea fisierelor de test
    # -------------------------------------------------------------------------

    def _adauga_functie_in_fisier(self, cale_fisier: Path, functie: str):
        """
        Adauga o functie noua intr-un fisier test_*.py.

        Daca fisierul contine deja comentariul final pentru testele initiale,
        acesta este scos temporar, functia este adaugata, apoi comentariul este
        repus la final.
        """
        continut_vechi = self._citeste_text(cale_fisier) if cale_fisier.exists() else ""
        avea_comentariu_final = self.COMENTARIU_FINAL_TESTE_INITIALE in continut_vechi

        continut_fara_final = continut_vechi.replace(
            self.COMENTARIU_FINAL_TESTE_INITIALE, ""
        ).rstrip()

        continut_nou = continut_fara_final
        if continut_nou:
            continut_nou += "\n\n"

        continut_nou += functie.strip() + "\n"

        if avea_comentariu_final:
            continut_nou = continut_nou.rstrip() + "\n\n"
            continut_nou += self.COMENTARIU_FINAL_TESTE_INITIALE + "\n"

        self._scrie_text(cale_fisier, continut_nou)

    def _elimina_functie_din_fisier(self, cale_fisier: Path, nume_functie: str):
        """
        Sterge din fisier functia cu numele dat.

        Expresia regulata cauta functia de la 'def test_...' pana la urmatoarea
        functie de test, la comentariul final sau pana la sfarsitul fisierului.
        """
        if not cale_fisier.exists():
            return

        continut = self._citeste_text(cale_fisier)
        pattern = (
            rf"\n{{0,2}}def\s+{re.escape(nume_functie)}\s*\(.*?"
            rf"(?=^\s*def\s+test_|^\s*#\s+Sfarsitul implementarii testelor initiale existente\.|\Z)"
        )
        continut_nou = re.sub(
            pattern,
            "\n",
            continut,
            flags=re.DOTALL | re.MULTILINE,
        ).rstrip() + "\n"

        self._scrie_text(cale_fisier, continut_nou)

    def _adauga_comentariu_final_teste_initiale(self):
        """
        Marcheaza toate fisierele test_*.py ca avand terminata etapa de
        introducere a testelor initiale.
        """
        for fisier_test_py in self.folder_curent.glob("test_*.py"):
            continut = self._citeste_text(fisier_test_py) if fisier_test_py.exists() else ""

            if self.COMENTARIU_FINAL_TESTE_INITIALE not in continut:
                continut = continut.rstrip()
                if continut:
                    continut += "\n\n"
                continut += self.COMENTARIU_FINAL_TESTE_INITIALE + "\n"
                self._scrie_text(fisier_test_py, continut)

    # -------------------------------------------------------------------------
    # Utilitare pentru scoruri si selectie
    # -------------------------------------------------------------------------

    def _scoruri_curente(self) -> tuple[float, float, float]:
        """Intoarce scorurile curente: pytest, coverage, cosmic-ray."""
        return (
            self.test_pytest(),
            self.test_coverage(),
            self.test_cosmic_ray(),
        )

    def _exista_imbunatatire(
        self,
        scoruri_inainte: tuple[float, float, float],
        scoruri_dupa: tuple[float, float, float],
    ) -> bool:
        """
        Intoarce True daca macar unul dintre scoruri a crescut.
        """
        return any(dupa > inainte for inainte, dupa in zip(scoruri_inainte, scoruri_dupa))

    def _format_imbunatatire(
        self,
        scoruri_inainte: tuple[float, float, float],
        scoruri_dupa: tuple[float, float, float],
    ) -> str:
        """
        Formateaza clar diferentele de scor dintre starea anterioara si cea
        ulterioara adaugarii unui test.
        """
        pytest_inainte, coverage_inainte, cosmic_inainte = scoruri_inainte
        pytest_dupa, coverage_dupa, cosmic_dupa = scoruri_dupa

        return (
            f"Pytest: {pytest_inainte}% -> {pytest_dupa}%; "
            f"Branch coverage: {coverage_inainte}% -> {coverage_dupa}%; "
            f"Cosmic-ray: {cosmic_inainte}% -> {cosmic_dupa}%."
        )

    def _solicita_functie_valida(
        self,
        mesaj_initial: str,
        deadline: float,
        mesaj_retransmitere: str,
    ) -> str | None:
        """
        Cere AI-ului o functie de test si continua sa o corecteze pana cand:
        - validate() intoarce 'Valid'
        - sau expira timpul alocat.

        Intoarce functia valida ca text sau None daca nu s-a reusit.
        """
        raspuns_ai = self.execute(mesaj_initial)
        rezultat_validare = self.validate(raspuns_ai)

        while rezultat_validare != "Valid" and time.time() < deadline:
            raspuns_ai = self.execute(
                rezultat_validare + "\n" + mesaj_retransmitere
            )
            rezultat_validare = self.validate(raspuns_ai)

        if rezultat_validare == "Valid":
            return raspuns_ai

        return None

    # -------------------------------------------------------------------------
    # Verificari initiale si jurnalizare
    # -------------------------------------------------------------------------

    def verifica_conditii_initiale(self):
        """
        Verifica toate dependintele minime necesare si pregateste structura de
        fisiere folosita ulterior de fluxul de testare.
        """
        fisier_de_testat = self.folder_curent / "to_test.py"
        if not fisier_de_testat.exists():
            raise FileNotFoundError(
                "Nu exista fisierul to_test.py, continand functia / clasa de testat"
            )

        fisier_config = self.folder_curent / ".aider.conf.yml"
        if not fisier_config.exists():
            raise FileNotFoundError("Nu exista fisierul .aider.conf.yml.")

        continut_config = self._citeste_text(fisier_config)
        if "read:" not in continut_config or "to_test.py" not in continut_config:
            raise ValueError(
                "Fisierul .aider.conf.yml nu contine configurarea read pentru to_test.py."
            )

        fisier_rules = self.folder_curent / "Rules.md"
        if not fisier_rules.exists():
            raise FileNotFoundError("Nu exista fisierul Rules.md.")

        continut_rules = self._linii(fisier_rules)
        numar_headere = sum(1 for linie in continut_rules if linie.startswith("#"))
        if numar_headere < 2:
            raise ValueError(
                "Fisierul Rules.md trebuie sa contina cel putin 2 randuri care incep cu #."
            )

        self.fisiere_testing_md = self._fisiere_testing_md()
        if not self.fisiere_testing_md:
            raise FileNotFoundError(
                "Nu exista niciun fisier testing_*.md cu categorii de teste."
            )

        for fisier_md in self.fisiere_testing_md:
            fisier_py = self._fisier_test_pentru_md(fisier_md)
            self.fisiere_testing[fisier_md.name] = fisier_py.name
            fisier_py.touch(exist_ok=True)

        folder_arh = self.folder_curent / "arh"
        folder_arh.mkdir(exist_ok=True)

    def log(
        self,
        categorie: str,
        regula: str,
        motivare: str,
        imbunatatire: str,
        autor: str = "AI",
    ):
        """
        Adauga o noua intrare in Logs.jsonl.

        Fisierul este append-only. Numarul intrarii este calculat pornind de la
        ultima intrare existenta.
        """
        fisier_log = self.folder_curent / "Logs.jsonl"
        numar_intrare = 1

        if fisier_log.exists() and fisier_log.stat().st_size > 0:
            with fisier_log.open("r", encoding="utf-8") as f:
                ultima_linie_valida = None
                for linie in f:
                    linie = linie.strip()
                    if linie:
                        ultima_linie_valida = linie

            if ultima_linie_valida is not None:
                ultima_intrare = json.loads(ultima_linie_valida)
                numar_intrare = int(ultima_intrare["Numar intrare"]) + 1

        intrare = {
            "Numar intrare": numar_intrare,
            "Categorie": categorie,
            "Regula": regula,
            "Motivare": motivare,
            "Imbunatatire": imbunatatire,
            "Data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Autor": autor,
        }

        with fisier_log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(intrare, ensure_ascii=False) + "\n")

    def arhiveaza(self):
        """
        Muta fisierul to_test.py si toate fisierele test_*.py intr-un nou
        subfolder numeric din /arh.
        """
        folder_arh = self.folder_curent / "arh"
        subfoldere = [x for x in folder_arh.iterdir() if x.is_dir()]

        numere_existente = []
        for subfolder in subfoldere:
            try:
                numar = int(subfolder.name.split(" ", 1)[0])
                numere_existente.append(numar)
            except (ValueError, IndexError):
                continue

        urmatorul_numar = max(numere_existente, default=0) + 1
        data_curenta = datetime.now().strftime("%d.%m.%Y %H:%M")
        folder_nou = folder_arh / f"{urmatorul_numar} {data_curenta}"
        folder_nou.mkdir()

        fisier_to_test = self.folder_curent / "to_test.py"
        if fisier_to_test.exists():
            fisier_to_test.rename(folder_nou / fisier_to_test.name)

        for fisier_test in self.folder_curent.glob("test_*.py"):
            if fisier_test.is_file():
                fisier_test.rename(folder_nou / fisier_test.name)

    def afiseaza_reguli_adaugate(self):
        """
        Afiseaza regulile noi adaugate in sesiunea curenta pe baza valorii
        self.numar_reguli_adaugate.
        """
        if self.numar_reguli_adaugate == 0:
            print(
                "Nu au fost identificate teste noi fata de tipurile deja existente in library-ul framework-ului de testare."
            )
            return

        fisier_log = self.folder_curent / "Logs.jsonl"
        if not fisier_log.exists() or fisier_log.stat().st_size == 0:
            print(f"Numar reguli adaugate: {self.numar_reguli_adaugate}")
            print("Logs.jsonl nu exista sau este gol.")
            return

        intrari = []
        with fisier_log.open("r", encoding="utf-8") as f:
            for linie in f:
                linie = linie.strip()
                if linie:
                    intrari.append(json.loads(linie))

        ultimele_intrari = intrari[-self.numar_reguli_adaugate:]

        print(f"Numar reguli adaugate: {self.numar_reguli_adaugate}")
        for intrare in ultimele_intrari:
            print(json.dumps(intrare, ensure_ascii=False, indent=2))

    # -------------------------------------------------------------------------
    # Interfata cu terminalul, Aider si Ollama
    # -------------------------------------------------------------------------

    def _ruleaza_comanda(
        self,
        comanda: str,
        timeout: int | None = None,
    ) -> subprocess.CompletedProcess:
        """
        Ruleaza o comanda shell in folderul curent si intoarce obiectul complet
        subprocess.CompletedProcess. Aceasta metoda este folosita intern acolo
        unde este nevoie si de codul de iesire.
        """
        return subprocess.run(
            comanda,
            shell=True,
            cwd=self.folder_curent,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def terminal(self, comanda: str):
        """
        Ruleaza o comanda shell si intoarce exact textul care s-ar vedea in
        terminal: stdout + stderr.
        """
        rezultat = self._ruleaza_comanda(comanda)
        return rezultat.stdout + rezultat.stderr

    def _citeste_pana_la_prompt(self):
        """
        Citeste iesirea procesului Aider pana cand:
        - apare promptul interactiv
        - sau expira timeout-ul de citire.
        """
        iesire = ""
        start = time.time()

        while time.time() - start < self.timeout_sec:
            if self.aider_process is None or self.aider_process.stdout is None:
                break

            gata, _, _ = select.select([self.aider_process.stdout], [], [], 0.2)

            if gata:
                bucata = os.read(
                    self.aider_process.stdout.fileno(),
                    4096,
                ).decode("utf-8", errors="replace")

                if not bucata:
                    break

                iesire += bucata

                if "\n> " in iesire or iesire.endswith("> "):
                    break

        return iesire

    def start_ai(self):
        """
        Porneste Ollama si Aider daca nu sunt deja active.

        Se porneste mai intai Ollama, apoi Aider. Dupa pornirea lui Aider se
        consuma promptul initial ca sa poata primi imediat comenzi.
        """
        if self.ollama_process is None or self.ollama_process.poll() is not None:
            self.ollama_process = subprocess.Popen(
                ["ollama", "serve"],
                cwd=self.folder_curent,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(2)

        if self.aider_process is None or self.aider_process.poll() is not None:
            self.aider_process = subprocess.Popen(
                ["aider"],
                cwd=self.folder_curent,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=False,
                bufsize=0,
            )
            self._citeste_pana_la_prompt()

    def reset_context(self):
        """
        Reseteaza contextul AI-ului prin inchiderea procesului Aider si
        repornirea lui. Ollama ramane pornit.
        """
        if self.aider_process is not None and self.aider_process.poll() is None:
            self.aider_process.terminate()
            try:
                self.aider_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.aider_process.kill()
                self.aider_process.wait()

        self.aider_process = None
        self.start_ai()

    def execute(self, comanda: str):
        """
        Trimite o comanda catre Aider-ul persistent si intoarce raspunsul brut
        citit pana la urmatorul prompt.
        """
        if self.aider_process is None or self.aider_process.poll() is not None:
            raise RuntimeError("Aider nu este pornit.")

        if self.aider_process.stdin is None:
            raise RuntimeError("Fluxul stdin al Aider nu este disponibil.")

        self.aider_process.stdin.write((comanda + "\n").encode("utf-8"))
        self.aider_process.stdin.flush()

        return self._citeste_pana_la_prompt()

    def stop_ai(self):
        """
        Opreste complet Aider si Ollama.
        """
        if self.aider_process is not None and self.aider_process.poll() is None:
            self.aider_process.terminate()
            try:
                self.aider_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.aider_process.kill()
                self.aider_process.wait()
        self.aider_process = None

        if self.ollama_process is not None and self.ollama_process.poll() is None:
            self.ollama_process.terminate()
            try:
                self.ollama_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.ollama_process.kill()
                self.ollama_process.wait()
        self.ollama_process = None

    # -------------------------------------------------------------------------
    # Validare tehnica a unui test furnizat de AI
    # -------------------------------------------------------------------------

    def validate(self, functie: str):
        """
        Verifica daca textul primit reprezinta strict o singura functie test_*
        valida din punct de vedere sintactic si executabila de pytest.

        Intoarce:
        - "Valid" daca testul este tehnic valid
        - mesajul brut de eroare in caz contrar
        """
        try:
            arbore = ast.parse(functie)
        except SyntaxError as eroare:
            return f"SyntaxError: {eroare}"

        functii_test = [
            nod for nod in arbore.body
            if isinstance(nod, ast.FunctionDef) and nod.name.startswith("test_")
        ]

        if len(functii_test) == 0:
            return (
                "The provided text does not contain any test function whose name starts with test_."
            )

        if len(functii_test) > 1:
            return (
                "The provided text contains multiple test functions. Only one test_* function is allowed."
            )

        if len(arbore.body) != 1 or not isinstance(arbore.body[0], ast.FunctionDef):
            return (
                "The provided text must contain exactly one test function and no additional code."
            )

        nume_functie = functii_test[0].name
        fisier_temp = self.folder_curent / "__validate_temp__.py"

        try:
            self._scrie_text(fisier_temp, functie.strip() + "\n")

            rezultat = self._ruleaza_comanda(
                f'python3 -m pytest -q "{fisier_temp.name}::{nume_functie}" --maxfail=1',
                timeout=self.timeout_sec,
            )
            iesire = rezultat.stdout + rezultat.stderr

            if rezultat.returncode in (0, 1):
                return "Valid"

            return iesire.strip() or f"Pytest validation failed with exit code {rezultat.returncode}."

        except subprocess.TimeoutExpired:
            return f"TimeoutError: the test did not finish within {self.timeout_sec} seconds."

        finally:
            if fisier_temp.exists():
                fisier_temp.unlink()

    # -------------------------------------------------------------------------
    # Metrici de evaluare a suitei de teste
    # -------------------------------------------------------------------------

    def test_pytest(self):
        """
        Ruleaza toate testele din fisierele test_*.py si intoarce procentul de
        teste PASSED raportat la totalul rezultatelor relevante raportate de
        pytest.
        """
        rezultat = self.terminal("python3 -m pytest -q test_*.py")

        if "no tests ran" in rezultat.lower():
            return 0.0

        linie_rezumat = None
        for linie in reversed(rezultat.splitlines()):
            if any(
                cuvant in linie
                for cuvant in [
                    "passed",
                    "failed",
                    "error",
                    "errors",
                    "skipped",
                    "xfailed",
                    "xpassed",
                ]
            ):
                linie_rezumat = linie.strip()
                break

        if linie_rezumat is None:
            return 0.0

        valori = {
            "passed": 0,
            "failed": 0,
            "error": 0,
            "errors": 0,
            "skipped": 0,
            "xfailed": 0,
            "xpassed": 0,
        }

        for cheie in valori:
            potrivire = re.search(rf"(\d+)\s+{cheie}\b", linie_rezumat)
            if potrivire:
                valori[cheie] = int(potrivire.group(1))

        numar_teste = sum(valori.values())
        if numar_teste == 0:
            return 0.0

        return round(valori["passed"] * 100 / numar_teste, 2)

    def test_coverage(self):
        """
        Ruleaza coverage cu --branch peste toate testele si extrage procentul de
        coverage pentru to_test.py.
        """
        self.terminal("python3 -m coverage erase")
        self.terminal("python3 -m coverage run --branch -m pytest -q test_*.py")
        rezultat_raport = self.terminal(
            'python3 -m coverage report -m --include="to_test.py"'
        )

        if "No data to report" in rezultat_raport:
            return 0.0

        linie_total = None
        for linie in rezultat_raport.splitlines():
            linie_strip = linie.strip()
            if linie_strip.startswith("TOTAL"):
                linie_total = linie_strip
                break

        if linie_total is None:
            for linie in rezultat_raport.splitlines():
                linie_strip = linie.strip()
                if linie_strip.startswith("to_test.py"):
                    linie_total = linie_strip
                    break

        if linie_total is None:
            return 0.0

        potrivire = re.search(r"(\d+%)\s*$", linie_total)
        if potrivire is None:
            return 0.0

        return float(potrivire.group(1).replace("%", ""))

    def test_cosmic_ray(self):
        """
        Ruleaza Cosmic Ray pe toata suita de teste si intoarce procentul de
        mutanti omorati.

        Formula folosita:
            scor = 100 - procent_supravietuitori
        """
        fisier_config = self.folder_curent / "__cosmic_ray__.toml"
        fisier_sesiune = self.folder_curent / "__cosmic_ray__.sqlite"
        fisier_baseline = self.folder_curent / "__cosmic_ray__.baseline.sqlite"

        for fisier in (fisier_config, fisier_sesiune, fisier_baseline):
            if fisier.exists():
                fisier.unlink()

        continut_config = (
            '[cosmic-ray]\n'
            'module-path = "to_test.py"\n'
            f'timeout = {self.timeout_sec}\n'
            'excluded-modules = []\n'
            'test-command = "python3 -m pytest -q test_*.py"\n\n'
            '[cosmic-ray.distributor]\n'
            'name = "local"\n'
        )

        try:
            self._scrie_text(fisier_config, continut_config)

            rezultat_init = self._ruleaza_comanda(
                f'cosmic-ray init "{fisier_config.name}" "{fisier_sesiune.name}"'
            )
            if rezultat_init.returncode != 0:
                return 0.0

            rezultat_baseline = self._ruleaza_comanda(
                f'cosmic-ray baseline "{fisier_sesiune.name}"'
            )
            if rezultat_baseline.returncode != 0:
                return 0.0

            rezultat_exec = self._ruleaza_comanda(
                f'cosmic-ray exec "{fisier_sesiune.name}"'
            )
            if rezultat_exec.returncode != 0:
                return 0.0

            rezultat_raport = self.terminal(f'cr-report "{fisier_sesiune.name}"')

            potrivire_supravietuitori = re.search(
                r"surviving mutants:\s*(\d+)\s*\(([\d.]+)%\)",
                rezultat_raport,
                flags=re.IGNORECASE,
            )
            if potrivire_supravietuitori:
                procent_supravietuitori = float(potrivire_supravietuitori.group(2))
                return round(100.0 - procent_supravietuitori, 2)

            potrivire_total = re.search(
                r"total jobs:\s*(\d+)",
                rezultat_raport,
                flags=re.IGNORECASE,
            )
            potrivire_supravietuitori_nr = re.search(
                r"surviving mutants:\s*(\d+)",
                rezultat_raport,
                flags=re.IGNORECASE,
            )

            if potrivire_total and potrivire_supravietuitori_nr:
                total = int(potrivire_total.group(1))
                supravietuitori = int(potrivire_supravietuitori_nr.group(1))

                if total == 0:
                    return 0.0

                return round((total - supravietuitori) * 100 / total, 2)

            return 0.0

        finally:
            for fisier in (fisier_config, fisier_sesiune, fisier_baseline):
                if fisier.exists():
                    fisier.unlink()

    # -------------------------------------------------------------------------
    # Etapa 1: scrierea testelor initiale deja descrise in fisierele testing_*.md
    # -------------------------------------------------------------------------

    def scrie_teste_initiale(self):
        """
        Parcurge toate categoriile si toate tipurile de teste deja enumerate in
        fisierele testing_*.md.

        Pentru fiecare regula numerotata:
        - cere AI-ului o functie de test
        - o valideaza tehnic
        - o adauga temporar in fisierul categoriei
        - o pastreaza doar daca imbunatateste macar un scor
        """
        instructiuni_generale = self._extrage_sectiune_dupa_header(
            self.folder_curent / "Rules.md",
            index_header=0,
            pana_la_urmatorul_header=True,
        )

        self.start_ai()

        try:
            for index_categorie, fisier_md in enumerate(self.fisiere_testing_md):
                reguli_generale_categorie = self._extrage_reguli_generale_categorie(
                    fisier_md
                )
                tipuri_teste = self._extrage_tipuri_teste(fisier_md)
                fisier_test_py = self._fisier_test_pentru_md(fisier_md)

                # Pentru context curat, la trecerea la o noua categorie
                # repornim doar Aider.
                if index_categorie > 0:
                    self.reset_context()

                for tip_test in tipuri_teste:
                    deadline = time.time() + self.timeout_sec
                    mesaj_initial = "\n".join(
                        [instructiuni_generale, reguli_generale_categorie, tip_test]
                    ).strip()

                    functie_valida = self._solicita_functie_valida(
                        mesaj_initial=mesaj_initial,
                        deadline=deadline,
                        mesaj_retransmitere=(
                            "Resend the corrected function and nothing else."
                        ),
                    )

                    if functie_valida is None:
                        continue

                    scoruri_inainte = self._scoruri_curente()
                    self._adauga_functie_in_fisier(fisier_test_py, functie_valida)
                    scoruri_dupa = self._scoruri_curente()

                    if self._exista_imbunatatire(scoruri_inainte, scoruri_dupa):
                        continue

                    nume_functie = self._extrage_nume_functie_test(functie_valida)
                    if nume_functie is not None:
                        self._elimina_functie_din_fisier(fisier_test_py, nume_functie)

            self._adauga_comentariu_final_teste_initiale()

        finally:
            self.stop_ai()

    # -------------------------------------------------------------------------
    # Etapa 2: cautarea de teste noi care nu sunt deja enumerate explicit
    # -------------------------------------------------------------------------

    def gaseste_teste_noi(self):
        """
        Pentru fiecare categorie:
        - porneste de la scorurile actuale
        - cere AI-ului teste noi care sa imbunatateasca suita existenta
        - valideaza tehnic fiecare test
        - pastreaza doar testele care cresc macar un scor
        - logheaza regulile noi pastrate
        - reseteaza contextul AI dupa fiecare succes
        - continua pana cand expira timpul categoriei
        """
        reguli_extinse = self._extrage_sectiune_dupa_header(
            self.folder_curent / "Rules.md",
            index_header=1,
            pana_la_urmatorul_header=False,
        )

        self.start_ai()

        try:
            for fisier_md in self.fisiere_testing_md:
                categorie = fisier_md.stem[len("testing_"):]
                fisier_test_py = self._fisier_test_pentru_md(fisier_md)
                deadline_categorie = time.time() + 10 * self.timeout_sec

                while True:
                    if time.time() >= deadline_categorie:
                        self.reset_context()
                        break

                    scoruri_inainte = self._scoruri_curente()

                    parti_mesaj = []
                    if reguli_extinse:
                        parti_mesaj.append(reguli_extinse)

                    for fisier_categorie in self.fisiere_testing_md:
                        continut = self._citeste_text(fisier_categorie).strip()
                        if continut:
                            parti_mesaj.append(continut)

                    parti_mesaj.append(
                        f"Current target category: {categorie}\n"
                        "Write exactly one new pytest test function for this category only.\n"
                        "It must improve the existing test suite for to_test.py.\n"
                        "Return only the Python function and nothing else."
                    )

                    mesaj_initial = "\n".join(parti_mesaj).strip()

                    functie_valida = self._solicita_functie_valida(
                        mesaj_initial=mesaj_initial,
                        deadline=deadline_categorie,
                        mesaj_retransmitere=(
                            "Resend only the corrected function and nothing else."
                        ),
                    )

                    if functie_valida is None:
                        self.reset_context()
                        break

                    nume_functie = self._extrage_nume_functie_test(functie_valida)
                    if nume_functie is None:
                        self.reset_context()
                        break

                    self._adauga_functie_in_fisier(fisier_test_py, functie_valida)
                    scoruri_dupa = self._scoruri_curente()

                    if not self._exista_imbunatatire(scoruri_inainte, scoruri_dupa):
                        self._elimina_functie_din_fisier(fisier_test_py, nume_functie)

                        if time.time() >= deadline_categorie:
                            self.reset_context()
                            break

                        functie_valida = self._solicita_functie_valida(
                            mesaj_initial=(
                                "The testing parameters were not improved. "
                                "Write a better test for the same category that improves the existing test suite. "
                                "Return only the Python test function."
                            ),
                            deadline=deadline_categorie,
                            mesaj_retransmitere=(
                                "Return only the corrected Python test function."
                            ),
                        )

                        if functie_valida is None:
                            self.reset_context()
                            break

                        nume_functie = self._extrage_nume_functie_test(functie_valida)
                        if nume_functie is None:
                            self.reset_context()
                            break

                        self._adauga_functie_in_fisier(fisier_test_py, functie_valida)
                        scoruri_dupa = self._scoruri_curente()

                        if not self._exista_imbunatatire(scoruri_inainte, scoruri_dupa):
                            self._elimina_functie_din_fisier(fisier_test_py, nume_functie)
                            continue

                    self.numar_reguli_adaugate += 1

                    imbunatatire = self._format_imbunatatire(
                        scoruri_inainte,
                        scoruri_dupa,
                    )

                    meta_info = self.execute(
                        "State exactly two fields in English on separate lines:\n"
                        f"Rule: the new testing rule implemented for category {categorie}, different from the existing ones.\n"
                        "Reasoning: the reasoning used to create or choose this new rule."
                    )

                    regula, motivare = self._extrage_regula_motivare(meta_info)

                    self.log(
                        categorie=categorie,
                        regula=regula,
                        motivare=motivare,
                        imbunatatire=imbunatatire,
                    )

                    # Dupa fiecare succes, se reseteaza AI-ul si se acorda din nou
                    # intreg intervalul pentru cautarea urmatoarei reguli noi.
                    self.reset_context()
                    deadline_categorie = time.time() + 10 * self.timeout_sec

        finally:
            self.stop_ai()


def main():
    """
    Punct de intrare minimal.

    Constructorul clasei AutoTesting ruleaza intregul flux, iar main doar
    instantiataza obiectul si gestioneaza erorile la nivel inalt.
    """
    try:
        AutoTesting()
    except (FileNotFoundError, ValueError, RuntimeError, subprocess.TimeoutExpired) as eroare:
        print(eroare)


if __name__ == "__main__":
    main()
