from __future__ import annotations

import json
import time
import urllib.error
from Includes.ollama_models import OllamaResponse


class OllamaGenerationMixin:
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

    def build_preview(self, text: str, limit: int = 200) -> str:
        """
        Returneaza un preview scurt al unui text, util pentru logging.

        Newline-urile sunt inlocuite cu spatii pentru afisare compacta.
        """
        compact_text = text.replace("\n", " ").strip()
        if len(compact_text) <= limit:
            return compact_text
        return compact_text[:limit] + "..."

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

        self.logger.ollama_prompt(prompt)
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
        self.logger.ai_debug(
            f"Timp generare raspuns: {round(self.last_execute_duration_sec, 2)}s"
        )
        self.logger.ollama_response(response_text)

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

    def execute(self, prompt: str) -> str:
        """
        Metoda de compatibilitate cu vechiul stil de apel din AutoTesting.py.

        Returneaza doar textul raspunsului, dar actualizeaza si
        `last_execute_duration_sec`.
        """
        response = self.generate(prompt)
        return response.text

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
