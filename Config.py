from __future__ import annotations

"""
Config.py

Rol
---
Acest fisier centralizeaza configurarea framework-ului de generare automata
de teste. Scopul lui este sa elimine valorile hardcodate din orchestrator si
din celelalte module, astfel incat:
- modificarile de configurare sa fie facute intr-un singur loc
- dependintele dintre module sa fie mai clare
- codul sa devina mai usor de intretinut si testat

Ce contine
----------
1. Starile folosite in fluxul principal:
   - generare teste initiale
   - generare teste noi
   - corectare propunere invalida

2. Timeout-urile si limitele de executie:
   - timeout pentru comenzi normale
   - timeout pentru mutmut
   - bugetul de timp maxim AI pe categorie
   - numarul de timp maxim de corectii
   - numarul de timp maxim de raspunsuri goale consecutive

3. Constante de lucru:
   - modelul Ollama implicit
   - importurile standard pentru fisierele de test
   - comentariul care marcheaza finalul testelor initiale
   - modelele de placeholder interzise in raspunsurile AI

4. Configurarea cailor importante din proiect:
   - folderul curent
   - fisierele principale
   - directoarele de lucru

Observatie
----------
Acest fisier nu executa logica de business. El doar furnizeaza configurarea
si caile standardizate necesare celorlalte module.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class States:
    """
    Grupeaza starile folosite in fluxul principal al aplicatiei.

    Valorile sunt pastrate numeric pentru a ramane compatibile cu logica deja
    existenta in AutoTesting.py.
    """

    TESTE_INITIALE: int = 1
    TESTE_NOI: int = 2
    CORECTEAZA_PROPUNERE: int = 3
    RULE_SI_REASONING: int = 4


@dataclass(frozen=True)
class Timeouts:
    """
    Grupeaza timeout-urile si limitele de executie.

    timeout_categorie_ai_sec este calculat implicit pe baza timeout_sec,
    exact ca in AutoTesting.py: 10 * timeout_sec.
    """

    timeout_sec: int = 180
    timeout_sec_mutmut: int = 600
    timeout_categorie_ai_sec: int = field(default=1800)
    max_corectie_attempts: int = 4
    max_empty_answers_consecutive: int = 2

    def __post_init__(self) -> None:
        # Daca se schimba timeout_sec, bugetul AI pe categorie se poate
        # recalcula automat, pastrand regula actuala din proiect.
        if self.timeout_categorie_ai_sec == 1800 and self.timeout_sec != 180:
            object.__setattr__(
                self,
                "timeout_categorie_ai_sec",
                10 * self.timeout_sec,
            )


@dataclass(frozen=True)
class FilesConfig:
    """
    Grupeaza numele standard ale fisierelor si directoarelor importante.

    Aceste valori sunt folosite de modulele care citesc, scriu, valideaza,
    logheaza sau arhiveaza artefactele proiectului.
    """

    rules_file_name: str = "Rules.md"
    file_under_test_name: str = "to_test.py"
    proposal_test_file_name: str = "test_propunere.py"
    archive_dir_name: str = "arh"
    accepted_rules_log_name: str = "Logs.jsonl"
    debug_dir_name: str = "logs"
    debug_log_name: str = "framework.log"
    ollama_log_name: str = "ollama_chat.log"
    validate_temp_file_name: str = "__validate_temp__.py"
    mutmut_cache_name: str = ".mutmut-cache"
    mutants_dir_name: str = "mutants"


@dataclass(frozen=True)
class TestRulesConfig:
    """
    Grupeaza regulile generale folosite la generarea si validarea testelor.
    """

    importuri_teste: str = "import pytest\nfrom to_test import *\n"
    comentariu_final_teste_initiale: str = (
        "# Sfarsitul implementarii testelor initiale existente."
    )
    prefix_testing_md: str = "testing_"
    prefix_test_py: str = "test_"

    placeholder_patterns: tuple[str, ...] = (
        "function_name",
        "valid_input",
        "invalid_input",
        "expected_output",
        "expected_error",
        "replace ",
        "replace`",
        "replace `",
        "actual function name",
        "actual inputs",
        "actual output",
        "your_function",
        "some_function",
        "placeholder",
    )


@dataclass(frozen=True)
class OllamaConfig:
    """
    Grupeaza configurarea pentru comunicarea cu Ollama.

    Valorile implicite sunt aliniate cu implementarea actuala din AutoTesting.py.
    """

    model: str = "qwen2.5-coder:7b"
    host: str = "127.0.0.1"
    port: int = 11434
    generate_endpoint: str = "/api/generate"
    tags_endpoint: str = "/api/tags"
    keep_alive: str = "5m"
    temperature: float = 0.1
    api_ready_timeout_sec: int = 3
    start_wait_timeout_sec: int = 20
    start_poll_interval_sec: float = 0.5


@dataclass(frozen=True)
class ProjectPaths:
    """
    Construieste toate caile importante pornind de la fisierul curent.

    De regula, current_file_path va fi dat de Path(__file__).resolve() din
    modulul care porneste aplicatia sau din orchestrator.
    """

    current_file_path: Path
    files: FilesConfig = field(default_factory=FilesConfig)

    @property
    def current_dir(self) -> Path:
        """Folderul in care ruleaza framework-ul."""
        return self.current_file_path.resolve().parent

    @property
    def rules_file(self) -> Path:
        """Fisierul cu regulile generale pentru generarea testelor."""
        return self.current_dir / self.files.rules_file_name

    @property
    def file_under_test(self) -> Path:
        """Fisierul Python care contine codul testat."""
        return self.current_dir / self.files.file_under_test_name

    @property
    def proposal_test_file(self) -> Path:
        """Fisierul temporar in care este scrisa propunerea curenta."""
        return self.current_dir / self.files.proposal_test_file_name

    @property
    def archive_dir(self) -> Path:
        """Directorul in care se arhiveaza artefactele finale."""
        return self.current_dir / self.files.archive_dir_name

    @property
    def accepted_rules_log_file(self) -> Path:
        """Fisierul JSONL in care sunt salvate regulile acceptate."""
        return self.current_dir / self.files.accepted_rules_log_name

    @property
    def debug_dir(self) -> Path:
        """Directorul dedicat logurilor tehnice."""
        return self.current_dir / self.files.debug_dir_name

    @property
    def debug_log_file(self) -> Path:
        """Fisierul text pentru logul general de debug."""
        return self.debug_dir / self.files.debug_log_name

    @property
    def ollama_log_file(self) -> Path:
        """Fisierul text pentru logul brut al interactiunilor cu Ollama."""
        return self.debug_dir / self.files.ollama_log_name

    @property
    def validate_temp_file(self) -> Path:
        """Fisierul temporar folosit la validarea unei propuneri."""
        return self.current_dir / self.files.validate_temp_file_name

    @property
    def mutmut_cache_path(self) -> Path:
        """Cache-ul creat de mutmut."""
        return self.current_dir / self.files.mutmut_cache_name

    @property
    def mutants_dir(self) -> Path:
        """Directorul mutants creat de mutmut."""
        return self.current_dir / self.files.mutants_dir_name


@dataclass(frozen=True)
class AppConfig:
    """
    Obiectul principal de configurare al aplicatiei.

    Acesta reuneste toate grupurile de configurare intr-un singur punct
    de acces, pentru a putea fi transmis simplu catre celelalte module.
    """

    current_file_path: Path
    states: States = field(default_factory=States)
    timeouts: Timeouts = field(default_factory=Timeouts)
    files: FilesConfig = field(default_factory=FilesConfig)
    test_rules: TestRulesConfig = field(default_factory=TestRulesConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)

    @property
    def paths(self) -> ProjectPaths:
        """Returneaza obiectul care expune toate caile standard ale proiectului."""
        return ProjectPaths(
            current_file_path=self.current_file_path,
            files=self.files,
        )