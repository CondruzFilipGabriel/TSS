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
    def __init__(self):
        self.auto_testing_path = Path(__file__).resolve()
        self.folder_curent = self.auto_testing_path.parent
        self.fisiere_testing = {}
        self.timeout_sec = 100
        self.numar_reguli_adaugate = 0
        self.aider_process = None
        self.ollama_process = None

        self.verifica_conditii_initiale()
        self.scrie_teste_initiale()
        self.gaseste_teste_noi()

        self.afiseaza_reguli_adaugate()


    def verifica_conditii_initiale(self):
        fisier_de_testat = self.folder_curent / "to_test.py"
        if not fisier_de_testat.exists():
            raise FileNotFoundError(
                "Nu exista fisierul to_test.py, continand functia / clasa de testat"
            )

        fisier_config = self.folder_curent / ".aider.conf.yml"
        if not fisier_config.exists():
            raise FileNotFoundError(
                "Nu exista fisierul .aider.conf.yml."
            )

        continut_config = fisier_config.read_text(encoding="utf-8")
        if "read:" not in continut_config or "to_test.py" not in continut_config:
            raise ValueError(
                "Fisierul .aider.conf.yml nu contine configurarea read pentru to_test.py."
            )

        fisier_rules = self.folder_curent / "Rules.md"
        if not fisier_rules.exists():
            raise FileNotFoundError(
                "Nu exista fisierul Rules.md."
            )

        continut_rules = fisier_rules.read_text(encoding="utf-8").splitlines()
        numar_headere = sum(1 for linie in continut_rules if linie.startswith("#"))
        if numar_headere < 2:
            raise ValueError(
                "Fisierul Rules.md trebuie sa contina cel putin 2 randuri care incep cu #."
            )

        fisiere_md = sorted(self.folder_curent.glob("testing_*.md"))
        if not fisiere_md:
            raise FileNotFoundError(
                "Nu exista niciun fisier testing_*.md cu categorii de teste."
            )

        for fisier_md in fisiere_md:
            nume_fara_prefix = fisier_md.stem[len("testing_"):]
            fisier_py = self.folder_curent / f"test_{nume_fara_prefix}.py"
            self.fisiere_testing[fisier_md.name] = fisier_py.name
            fisier_py.touch(exist_ok=True)

        folder_arh = self.folder_curent / "arh"
        folder_arh.mkdir(exist_ok=True)


    def scrie_teste_initiale(self):
        def extrage_sectiune_dupa_primul_header(cale_md: Path):
            linii = cale_md.read_text(encoding="utf-8").splitlines()
            start = None
            end = len(linii)

            for i, linie in enumerate(linii):
                if linie.startswith("# "):
                    start = i + 1
                    break

            if start is None:
                return ""

            for i in range(start, len(linii)):
                if linii[i].startswith("# "):
                    end = i
                    break

            return "\n".join(linii[start:end]).strip()

        def extrage_reguli_generale_categorie(cale_md: Path):
            linii = cale_md.read_text(encoding="utf-8").splitlines()
            start = None
            end = len(linii)

            for i, linie in enumerate(linii):
                if linie.startswith("# "):
                    start = i + 1
                    break

            if start is None:
                return ""

            for i in range(start, len(linii)):
                if linii[i].startswith("1."):
                    end = i
                    break

            return "\n".join(linii[start:end]).strip()

        def extrage_tipuri_teste(cale_md: Path):
            linii = cale_md.read_text(encoding="utf-8").splitlines()
            tipuri = []

            for linie in linii:
                linie_strip = linie.strip()
                potrivire = re.match(r"^\d+\.\s*(.+)$", linie_strip)
                if potrivire:
                    tipuri.append(potrivire.group(1).strip())

            return tipuri

        def adauga_functie_in_fisier(cale_fisier: Path, functie: str):
            continut_vechi = ""
            if cale_fisier.exists():
                continut_vechi = cale_fisier.read_text(encoding="utf-8")

            continut_nou = continut_vechi.rstrip()
            if continut_nou:
                continut_nou += "\n\n"
            continut_nou += functie.strip() + "\n"

            cale_fisier.write_text(continut_nou, encoding="utf-8")

        def elimina_functie_din_fisier(cale_fisier: Path, nume_functie: str):
            if not cale_fisier.exists():
                return

            continut = cale_fisier.read_text(encoding="utf-8")
            pattern = rf"\n{{0,2}}def\s+{re.escape(nume_functie)}\s*\(.*?(?=^\s*def\s+test_|^\s*#\s+Sfarsitul implementarii testelor initiale existente\.|\Z)"
            continut_nou = re.sub(pattern, "\n", continut, flags=re.DOTALL | re.MULTILINE).rstrip() + "\n"
            cale_fisier.write_text(continut_nou, encoding="utf-8")

        def extrage_nume_functie(functie: str):
            potrivire = re.search(r"def\s+(test_[A-Za-z0-9_]+)\s*\(", functie)
            if potrivire:
                return potrivire.group(1)
            return None

        instructiuni_generale = extrage_sectiune_dupa_primul_header(self.folder_curent / "Rules.md")
        fisiere_md = sorted(self.folder_curent.glob("testing_*.md"))

        self.start_ai()

        try:
            for index_categorie, fisier_md in enumerate(fisiere_md):
                reguli_generale_categorie = extrage_reguli_generale_categorie(fisier_md)
                tipuri_teste = extrage_tipuri_teste(fisier_md)
                fisier_test_py = self.folder_curent / self.fisiere_testing[fisier_md.name]

                if index_categorie > 0:
                    self.reset_context()

                for tip_test in tipuri_teste:
                    deadline = time.time() + self.timeout_sec

                    mesaj_initial = "\n".join([
                        instructiuni_generale,
                        reguli_generale_categorie,
                        tip_test
                    ]).strip()

                    raspuns_ai = self.execute(mesaj_initial)
                    rezultat_validare = self.validate(raspuns_ai)

                    while rezultat_validare != "Valid" and time.time() < deadline:
                        mesaj_eroare = (
                            rezultat_validare
                            + "\nRetransmite functia corectata si nimic altceva."
                        )
                        raspuns_ai = self.execute(mesaj_eroare)
                        rezultat_validare = self.validate(raspuns_ai)

                    if rezultat_validare != "Valid":
                        continue

                    scor_pytest_inainte = self.test_pytest()
                    scor_coverage_inainte = self.test_coverage()
                    scor_cosmic_inainte = self.test_cosmic_ray()

                    adauga_functie_in_fisier(fisier_test_py, raspuns_ai)

                    scor_pytest_dupa = self.test_pytest()
                    scor_coverage_dupa = self.test_coverage()
                    scor_cosmic_dupa = self.test_cosmic_ray()

                    if (
                        scor_pytest_dupa > scor_pytest_inainte
                        or scor_coverage_dupa > scor_coverage_inainte
                        or scor_cosmic_dupa > scor_cosmic_inainte
                    ):
                        continue

                    nume_functie = extrage_nume_functie(raspuns_ai)
                    if nume_functie is not None:
                        elimina_functie_din_fisier(fisier_test_py, nume_functie)

            for fisier_test_py in self.folder_curent.glob("test_*.py"):
                continut = fisier_test_py.read_text(encoding="utf-8") if fisier_test_py.exists() else ""
                comentariu_final = "# Sfarsitul implementarii testelor initiale existente."

                if comentariu_final not in continut:
                    continut = continut.rstrip()
                    if continut:
                        continut += "\n\n"
                    continut += comentariu_final + "\n"
                    fisier_test_py.write_text(continut, encoding="utf-8")

        finally:
            self.stop_ai()


    def gaseste_teste_noi(self):
        def extrage_reguli_extinse():
            linii = (self.folder_curent / "Rules.md").read_text(encoding="utf-8").splitlines()
            pozitii_headere = [i for i, linie in enumerate(linii) if linie.startswith("# ")]
            if len(pozitii_headere) < 2:
                return ""
            return "\n".join(linii[pozitii_headere[1] + 1:]).strip()

        def adauga_functie_in_fisier(cale_fisier: Path, functie: str):
            continut_vechi = ""
            if cale_fisier.exists():
                continut_vechi = cale_fisier.read_text(encoding="utf-8")

            comentariu_final = "# Sfarsitul implementarii testelor initiale existente."
            continut_fara_final = continut_vechi.replace(comentariu_final, "").rstrip()

            continut_nou = continut_fara_final
            if continut_nou:
                continut_nou += "\n\n"
            continut_nou += functie.strip() + "\n\n" + comentariu_final + "\n"

            cale_fisier.write_text(continut_nou, encoding="utf-8")

        def elimina_functie_din_fisier(cale_fisier: Path, nume_functie: str):
            if not cale_fisier.exists():
                return

            continut = cale_fisier.read_text(encoding="utf-8")
            pattern = rf"\n{{0,2}}def\s+{re.escape(nume_functie)}\s*\(.*?(?=^\s*def\s+test_|^\s*#\s+Sfarsitul implementarii testelor initiale existente\.|\Z)"
            continut_nou = re.sub(pattern, "\n", continut, flags=re.DOTALL | re.MULTILINE).rstrip() + "\n"
            cale_fisier.write_text(continut_nou, encoding="utf-8")

        def extrage_nume_functie(functie: str):
            potrivire = re.search(r"def\s+(test_[A-Za-z0-9_]+)\s*\(", functie)
            if potrivire:
                return potrivire.group(1)
            return None

        def scoruri_curente():
            return (
                self.test_pytest(),
                self.test_coverage(),
                self.test_cosmic_ray(),
            )

        def format_imbunatatire(pytest_inainte, cov_inainte, cosmic_inainte,
                                pytest_dupa, cov_dupa, cosmic_dupa):
            return (
                f"Pytest: {pytest_inainte}% -> {pytest_dupa}%; "
                f"Branch coverage: {cov_inainte}% -> {cov_dupa}%; "
                f"Cosmic-ray: {cosmic_inainte}% -> {cosmic_dupa}%."
            )

        def extrage_regula_motivare(text: str):
            linii = [linie.strip() for linie in text.splitlines() if linie.strip()]
            regula = ""
            motivare = ""

            for i, linie in enumerate(linii):
                lower = linie.lower()
                if lower.startswith("rule:") or lower.startswith("regula:"):
                    regula = linie.split(":", 1)[1].strip()
                elif lower.startswith("reasoning:") or lower.startswith("motivation:") or lower.startswith("motivare:"):
                    motivare = linie.split(":", 1)[1].strip()
                    if i + 1 < len(linii):
                        rest = [x for x in linii[i + 1:] if not x.lower().startswith(("rule:", "regula:", "reasoning:", "motivation:", "motivare:"))]
                        if rest:
                            motivare = (motivare + "\n" + "\n".join(rest)).strip()

            if not regula and linii:
                regula = linii[0]
            if not motivare and len(linii) > 1:
                motivare = "\n".join(linii[1:]).strip()

            return regula, motivare

        pytest_initial, coverage_initial, cosmic_initial = scoruri_curente()
        reguli_extinse = extrage_reguli_extinse()
        fisiere_md = sorted(self.folder_curent.glob("testing_*.md"))

        self.start_ai()

        try:
            for fisier_md in fisiere_md:
                categorie = fisier_md.stem[len("testing_"):]
                fisier_test_py = self.folder_curent / self.fisiere_testing[fisier_md.name]

                deadline_categorie = time.time() + 10 * self.timeout_sec

                while True:
                    if time.time() >= deadline_categorie:
                        self.reset_context()
                        break

                    scor_pytest_inainte, scor_coverage_inainte, scor_cosmic_inainte = scoruri_curente()

                    parti_mesaj = []
                    if reguli_extinse:
                        parti_mesaj.append(reguli_extinse)

                    for fisier_categorie in fisiere_md:
                        continut = fisier_categorie.read_text(encoding="utf-8").strip()
                        if continut:
                            parti_mesaj.append(continut)

                    parti_mesaj.append(
                        f"Current target category: {categorie}\n"
                        f"Write exactly one new pytest test function for this category only.\n"
                        f"It must improve the existing test suite for to_test.py.\n"
                        f"Return only the Python function and nothing else."
                    )

                    mesaj_initial = "\n".join(parti_mesaj).strip()

                    raspuns_ai = self.execute(mesaj_initial)
                    rezultat_validare = self.validate(raspuns_ai)

                    while rezultat_validare != "Valid" and time.time() < deadline_categorie:
                        raspuns_ai = self.execute(
                            rezultat_validare
                            + "\nRetransmite doar functia corectata si nimic altceva."
                        )
                        rezultat_validare = self.validate(raspuns_ai)

                    if rezultat_validare != "Valid":
                        self.reset_context()
                        break

                    nume_functie = extrage_nume_functie(raspuns_ai)
                    if nume_functie is None:
                        self.reset_context()
                        break

                    adauga_functie_in_fisier(fisier_test_py, raspuns_ai)

                    scor_pytest_dupa, scor_coverage_dupa, scor_cosmic_dupa = scoruri_curente()

                    exista_imbunatatire = (
                        scor_pytest_dupa > scor_pytest_inainte
                        or scor_coverage_dupa > scor_coverage_inainte
                        or scor_cosmic_dupa > scor_cosmic_inainte
                    )

                    if not exista_imbunatatire:
                        elimina_functie_din_fisier(fisier_test_py, nume_functie)

                        if time.time() >= deadline_categorie:
                            self.reset_context()
                            break

                        raspuns_ai = self.execute(
                            "The testing parameters were not improved. "
                            "Write a better test for the same category that improves the existing test suite. "
                            "Return only the Python test function."
                        )
                        rezultat_validare = self.validate(raspuns_ai)

                        while rezultat_validare != "Valid" and time.time() < deadline_categorie:
                            raspuns_ai = self.execute(
                                rezultat_validare
                                + "\nReturn only the corrected Python test function."
                            )
                            rezultat_validare = self.validate(raspuns_ai)

                        if rezultat_validare != "Valid":
                            self.reset_context()
                            break

                        nume_functie = extrage_nume_functie(raspuns_ai)
                        if nume_functie is None:
                            self.reset_context()
                            break

                        adauga_functie_in_fisier(fisier_test_py, raspuns_ai)

                        scor_pytest_dupa, scor_coverage_dupa, scor_cosmic_dupa = scoruri_curente()

                        exista_imbunatatire = (
                            scor_pytest_dupa > scor_pytest_inainte
                            or scor_coverage_dupa > scor_coverage_inainte
                            or scor_cosmic_dupa > scor_cosmic_inainte
                        )

                        if not exista_imbunatatire:
                            elimina_functie_din_fisier(fisier_test_py, nume_functie)
                            continue

                    self.numar_reguli_adaugate += 1

                    imbunatatire = format_imbunatatire(
                        scor_pytest_inainte, scor_coverage_inainte, scor_cosmic_inainte,
                        scor_pytest_dupa, scor_coverage_dupa, scor_cosmic_dupa
                    )

                    meta_info = self.execute(
                        "State exactly two fields in English on separate lines:\n"
                        f"Rule: the new testing rule implemented for category {categorie}, different from the existing ones.\n"
                        "Reasoning: the reasoning used to create or choose this new rule."
                    )

                    regula, motivare = extrage_regula_motivare(meta_info)

                    self.log(
                        categorie=categorie,
                        regula=regula,
                        motivare=motivare,
                        imbunatatire=imbunatatire,
                    )

                    pytest_initial, coverage_initial, cosmic_initial = (
                        scor_pytest_dupa,
                        scor_coverage_dupa,
                        scor_cosmic_dupa,
                    )

                    self.reset_context()
                    deadline_categorie = time.time() + 10 * self.timeout_sec

        finally:
            self.stop_ai()


    # motivare = logica / rationamentul pentru care a adaugat regula noua
    # imbunatatire = performanta pe care a crescut-o si valorile initiale si finale
    def log(self, categorie: str, regula: str, motivare: str, imbunatatire : str, autor: str = "AI"):
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
        if self.numar_reguli_adaugate == 0:
            print("Nu au fost identificate teste noi fata de tipurile deja existente in library-ul framework-ului de testare.")
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

    
    def terminal(self, comanda: str):
        rezultat = subprocess.run(
            comanda,
            shell=True,
            cwd=self.folder_curent,
            capture_output=True,
            text=True
        )

        return rezultat.stdout + rezultat.stderr
    

    def _citeste_pana_la_prompt(self):
        iesire = ""
        start = time.time()

        while time.time() - start < self.timeout_sec:
            gata, _, _ = select.select([self.aider_process.stdout], [], [], 0.2)

            if gata:
                bucata = os.read(self.aider_process.stdout.fileno(), 4096).decode("utf-8", errors="replace")
                if not bucata:
                    break

                iesire += bucata

                if "\n> " in iesire or iesire.endswith("> "):
                    break
            else:
                continue

        return iesire


    def start_ai(self):
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
        if self.aider_process is None or self.aider_process.poll() is not None:
            raise RuntimeError("Aider nu este pornit.")

        self.aider_process.stdin.write((comanda + "\n").encode("utf-8"))
        self.aider_process.stdin.flush()

        return self._citeste_pana_la_prompt()


    def stop_ai(self):
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

    def validate(self, functie: str):
        try:
            arbore = ast.parse(functie)
        except SyntaxError as e:
            return f"SyntaxError: {e}"

        functii_test = [
            nod for nod in arbore.body
            if isinstance(nod, ast.FunctionDef) and nod.name.startswith("test_")
        ]

        if len(functii_test) == 0:
            return "Functia transmisa nu contine nicio functie de test care sa inceapa cu test_."

        if len(functii_test) > 1:
            return "Functia transmisa contine mai multe functii de test. Este permisa o singura functie test_*."

        if len(arbore.body) != 1 or not isinstance(arbore.body[0], ast.FunctionDef):
            return "Textul transmis trebuie sa contina strict o singura functie de test, fara alt cod suplimentar."

        nume_functie = functii_test[0].name
        fisier_temp = self.folder_curent / "__validate_temp__.py"

        try:
            fisier_temp.write_text(functie + "\n", encoding="utf-8")

            rezultat = self.terminal(
                f'python3 -m pytest -q "{fisier_temp.name}::{nume_functie}" --maxfail=1'
            )

            if "ERROR collecting" in rezultat:
                return rezultat
            if "found no collectors" in rezultat:
                return rezultat
            if "ImportError" in rezultat:
                return rezultat
            if "SyntaxError" in rezultat:
                return rezultat
            if "NameError" in rezultat:
                return rezultat
            if "TypeError" in rezultat and " failed" not in rezultat.lower():
                return rezultat
            if "ERROR " in rezultat or "\nERROR" in rezultat:
                return rezultat

            if "1 passed" in rezultat or "1 failed" in rezultat:
                return "Valid"

            return rezultat

        finally:
            if fisier_temp.exists():
                fisier_temp.unlink()

    def test_pytest(self):
        rezultat = self.terminal("python3 -m pytest -q test_*.py")

        if "no tests ran" in rezultat.lower():
            return 0.0

        linie_rezumat = None
        for linie in reversed(rezultat.splitlines()):
            if any(cuvant in linie for cuvant in [
                "passed", "failed", "error", "errors", "skipped",
                "xfailed", "xpassed"
            ]):
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

        numar_teste = (
            valori["passed"] +
            valori["failed"] +
            valori["error"] +
            valori["errors"] +
            valori["skipped"] +
            valori["xfailed"] +
            valori["xpassed"]
        )

        if numar_teste == 0:
            return 0.0

        return round(valori["passed"] * 100 / numar_teste, 2)


    def test_coverage(self):
        self.terminal("python3 -m coverage erase")

        rezultat_rulare = self.terminal(
            "python3 -m coverage run --branch -m pytest -q test_*.py"
        )

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
        fisier_config = self.folder_curent / "__cosmic_ray__.toml"
        fisier_sesiune = self.folder_curent / "__cosmic_ray__.sqlite"
        fisier_baseline = self.folder_curent / "__cosmic_ray__.baseline.sqlite"

        if fisier_config.exists():
            fisier_config.unlink()
        if fisier_sesiune.exists():
            fisier_sesiune.unlink()
        if fisier_baseline.exists():
            fisier_baseline.unlink()

        continut_config = f"""
            [cosmic-ray]
            module-path = "to_test.py"
            timeout = {self.timeout_sec}
            excluded-modules = []
            test-command = "python3 -m pytest -q test_*.py"

            [cosmic-ray.distributor]
            name = "local"
        """.strip()

        try:
            fisier_config.write_text(continut_config + "\n", encoding="utf-8")

            rezultat_init = self.terminal(
                f'cosmic-ray init "{fisier_config.name}" "{fisier_sesiune.name}"'
            )

            rezultat_baseline = self.terminal(
                f'cosmic-ray baseline --report "{fisier_config.name}" "{fisier_sesiune.name}"'
            )

            if (
                "failed" in rezultat_baseline.lower()
                or "error" in rezultat_baseline.lower()
                or "works fine" not in rezultat_baseline.lower()
            ):
                return 0.0

            rezultat_exec = self.terminal(
                f'cosmic-ray exec "{fisier_config.name}" "{fisier_sesiune.name}"'
            )

            rezultat_raport = self.terminal(
                f'cr-report "{fisier_sesiune.name}"'
            )

            potrivire_supravietuitori = re.search(
                r"surviving mutants:\s*(\d+)\s*\(([\d.]+)%\)",
                rezultat_raport,
                flags=re.IGNORECASE
            )
            if potrivire_supravietuitori:
                procent_supravietuitori = float(potrivire_supravietuitori.group(2))
                return round(100.0 - procent_supravietuitori, 2)

            potrivire_total = re.search(
                r"total jobs:\s*(\d+)",
                rezultat_raport,
                flags=re.IGNORECASE
            )
            potrivire_supravietuitori_nr = re.search(
                r"surviving mutants:\s*(\d+)",
                rezultat_raport,
                flags=re.IGNORECASE
            )

            if potrivire_total and potrivire_supravietuitori_nr:
                total = int(potrivire_total.group(1))
                supravietuitori = int(potrivire_supravietuitori_nr.group(1))

                if total == 0:
                    return 0.0

                return round((total - supravietuitori) * 100 / total, 2)

            return 0.0

        finally:
            if fisier_config.exists():
                fisier_config.unlink()
            if fisier_sesiune.exists():
                fisier_sesiune.unlink()
            if fisier_baseline.exists():
                fisier_baseline.unlink()


def main():
    try:
        auto_testing = AutoTesting()
    except FileNotFoundError as eroare:
        print(eroare)


if __name__ == "__main__":
    main()