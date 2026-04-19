from __future__ import annotations

"""
OllamaClient.py

Rol
---
Acest fisier gestioneaza toata comunicarea framework-ului cu serverul local
Ollama. Scopul lui este sa scoata din orchestrator responsabilitatile legate de:
- verificarea disponibilitatii API-ului
- pornirea serverului local Ollama, daca este nevoie
- oprirea serverului, daca a fost pornit de framework
- trimiterea unui prompt catre model
- primirea raspunsului brut
- logarea interactiunii si a timpului de generatie

Observatii
----------
1. Acest modul nu construieste prompturile. Asta este responsabilitatea
   lui PromptBuilder.py.

2. Acest modul nu parseaza raspunsurile. Asta este responsabilitatea
   lui ResponseParser.py.

3. Acest modul nu valideaza functiile generate si nu scrie fisiere.
   El doar trimite promptul si returneaza raspunsul brut.

4. Serverul Ollama este oprit doar daca a fost pornit de acest framework.
   Daca API-ul era deja disponibil, nu se intervine asupra lui la final.
"""

import json
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from Config import AppConfig
from Logger import Logger


@dataclass(frozen=True)
class OllamaResponse:
    """
    Reprezinta raspunsul returnat de o singura cerere catre Ollama.

    Campuri:
    - text: raspunsul brut al modelului
    - duration_sec: timpul masurat pentru cererea de generare
    - model: modelul folosit pentru generare
    """

    text: str
    duration_sec: float
    model: str


class OllamaClient:
    """
    Client pentru serverul local Ollama.

    Responsabilitati:
    - verifica daca API-ul local este disponibil
    - porneste `ollama serve` daca este necesar
    - trimite cereri catre endpoint-urile relevante
    - opreste procesul pornit de framework
    - logheaza informatii utile pentru debugging

    Parametri:
    - config: configurarea centrala a aplicatiei
    - logger: logger-ul folosit pentru debug si loguri tehnice
    """

    def __init__(self, config: AppConfig, logger: Logger) -> None:
        self.config = config
        self.logger = logger

        # Procesul Ollama pornit de framework, daca a fost necesar.
        self._ollama_process: Optional[subprocess.Popen] = None

        # Flag care marcheaza explicit daca acest client a pornit serverul.
        self._started_by_framework: bool = False

        # Ultima durata a unei executii de generare.
        self.last_execute_duration_sec: float = 0.0

    # ------------------------------------------------------------------
    # Helpers interne pentru URL-uri si request-uri
    # ------------------------------------------------------------------

    def _build_url(self, endpoint: str) -> str:
        """
        Construieste URL-ul complet pentru un endpoint Ollama.
        """
        host = self.config.ollama.host
        port = self.config.ollama.port
        return f"http://{host}:{port}{endpoint}"

    def _http_request(
        self,
        endpoint: str,
        payload: dict | None = None,
        timeout: int = 10,
    ) -> dict:
        """
        Executa o cerere HTTP catre API-ul local Ollama.

        Daca payload este furnizat:
        - se face request POST
        - corpul este serializat JSON

        Altfel:
        - se face request GET

        Returneaza raspunsul JSON decodat ca dictionar.
        """
        url = self._build_url(endpoint)
        data = None
        headers: dict[str, str] = {}
        method = "GET"

        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
            method = "POST"

        request = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method=method,
        )

        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            if not body:
                return {}
            return json.loads(body)

    # ------------------------------------------------------------------
    # Verificarea disponibilitatii API-ului
    # ------------------------------------------------------------------

    def is_api_ready(self) -> bool:
        """
        Verifica daca API-ul local Ollama raspunde.

        Se foloseste endpoint-ul /api/tags, exact ca in implementarea initiala.
        """
        try:
            self._http_request(
                endpoint=self.config.ollama.tags_endpoint,
                timeout=self.config.ollama.api_ready_timeout_sec,
            )
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Pornirea si oprirea serverului local Ollama
    # ------------------------------------------------------------------

    def start(self) -> None:
        """
        Porneste serverul local Ollama doar daca API-ul nu este deja disponibil.

        In terminal afisam doar mesaje scurte si corecte semantic:
        - mai intai verificam daca API-ul este activ
        - afisam mesajul de pornire doar daca trebuie intr-adevar sa lansam procesul
        """
        if self.is_api_ready():
            self.logger.ai("API-ul Ollama este activ.")
            return

        self.logger.ai("pornesc Ollama...")

        if self._ollama_process is None or self._ollama_process.poll() is not None:
            self._ollama_process = subprocess.Popen(
                ["ollama", "serve"],
                cwd=self.config.paths.current_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._started_by_framework = True

        start_time = time.monotonic()
        timeout_sec = self.config.ollama.start_wait_timeout_sec
        poll_interval = self.config.ollama.start_poll_interval_sec

        while time.monotonic() - start_time < timeout_sec:
            if self.is_api_ready():
                self.logger.ai("API-ul Ollama este activ.")
                return
            time.sleep(poll_interval)

        raise RuntimeError("Ollama API nu a devenit disponibila in timp util.")
    

    def stop(self) -> None:
        """
        Opreste serverul Ollama doar daca a fost pornit de acest framework.
        """
        self.logger.ai("opresc uneltele AI...")

        if not self._started_by_framework:
            self._ollama_process = None
            return

        if self._ollama_process is not None and self._ollama_process.poll() is None:
            self._ollama_process.terminate()
            try:
                self._ollama_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._ollama_process.kill()
                self._ollama_process.wait()

        self._ollama_process = None
        self._started_by_framework = False


    def reset_context(self) -> None:
        """
        Marcheaza logic resetarea contextului.

        In fluxul actual, cererile sunt one-shot si independente.
        In terminal afisam un mesaj scurt, iar detaliile raman in logul de debug.
        """
        self.logger.ai("resetez contextul.")


    # ------------------------------------------------------------------
    # Selectia modelului si payload-ul de generare
    # ------------------------------------------------------------------

    def get_model_name(self) -> str:
        """
        Returneaza numele modelului configurat pentru generare.
        """
        return self.config.ollama.model

    def build_generate_payload(self, prompt: str) -> dict:
        """
        Construieste payload-ul trimis la endpoint-ul de generare.
        """
        return {
            "model": self.get_model_name(),
            "prompt": prompt,
            "stream": False,
            "keep_alive": self.config.ollama.keep_alive,
            "options": {
                "temperature": self.config.ollama.temperature,
            },
        }

    # ------------------------------------------------------------------
    # Utilitar pentru preview scurt de text
    # ------------------------------------------------------------------

    def build_preview(self, text: str, limit: int = 200) -> str:
        """
        Returneaza un preview scurt al unui text, util pentru logging.

        Newline-urile sunt inlocuite cu spatii pentru afisare compacta.
        """
        compact_text = text.replace("\n", " ").strip()
        if len(compact_text) <= limit:
            return compact_text
        return compact_text[:limit] + "..."


    # ------------------------------------------------------------------
    # Generare efectiva prin Ollama
    # ------------------------------------------------------------------

    def generate(self, prompt: str) -> OllamaResponse:
        """
        Trimite un prompt catre Ollama si returneaza raspunsul brut.

        In terminal:
        - afisam doar mesaje scurte si utile
        - nu afisam preview-uri sau lungimi de text

        In logul de debug:
        - pastram toate detaliile tehnice
        """
        self.start()

        self.logger.ai("trimit instructiunea catre Ollama...")
        self.logger.ai_debug(f"Lungime prompt: {len(prompt)} caractere.")
        self.logger.ai_debug(
            f"Preview prompt: {self.build_preview(prompt, limit=300)}"
        )

        payload = self.build_generate_payload(prompt)

        try:
            start_time = time.monotonic()
            response_data = self._http_request(
                endpoint=self.config.ollama.generate_endpoint,
                payload=payload,
                timeout=self.config.timeouts.timeout_sec,
            )
            self.last_execute_duration_sec = time.monotonic() - start_time
        except urllib.error.HTTPError as exception:
            body = exception.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Ollama HTTPError {exception.code}: {body}"
            ) from exception
        except urllib.error.URLError as exception:
            raise RuntimeError(
                f"Nu se poate accesa API-ul Ollama: {exception}"
            ) from exception

        response_text = response_data.get("response", "") or ""
        model_name = self.get_model_name()

        self.logger.ai_debug(
            f"Lungime output brut: {len(response_text)} caractere."
        )
        self.logger.ai_debug(
            f"Preview output brut: {self.build_preview(response_text, limit=300)}"
        )
        self.logger.ai(
            f"timp generare raspuns: {round(self.last_execute_duration_sec, 2)}s"
        )

        self.logger.append_ollama_chat(
            prompt=prompt,
            response=response_text,
            model=model_name,
            duration_sec=self.last_execute_duration_sec,
        )

        return OllamaResponse(
            text=response_text,
            duration_sec=self.last_execute_duration_sec,
            model=model_name,
        )


    # ------------------------------------------------------------------
    # Compatibilitate cu stilul vechi din AutoTesting.py
    # ------------------------------------------------------------------

    def execute(self, prompt: str) -> str:
        """
        Metoda de compatibilitate cu vechiul stil de apel din AutoTesting.py.

        Returneaza doar textul raspunsului, dar actualizeaza si
        `last_execute_duration_sec`.
        """
        response = self.generate(prompt)
        return response.text

    # ------------------------------------------------------------------
    # Curatare controlata a resurselor
    # ------------------------------------------------------------------

    def close(self) -> None:
        """
        Inchide resursele controlate de client.

        In prezent, asta inseamna oprirea procesului Ollama pornit de framework.
        """
        self.stop()

    def __enter__(self) -> "OllamaClient":
        """
        Permite folosirea clientului in context manager.
        """
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """
        Asigura eliberarea resurselor la iesirea din context manager.
        """
        self.close()