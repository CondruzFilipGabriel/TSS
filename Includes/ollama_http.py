from __future__ import annotations
import json
import urllib.error
import urllib.request


class OllamaHttpMixin:
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
