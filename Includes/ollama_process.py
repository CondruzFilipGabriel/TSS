from __future__ import annotations

import subprocess
import time


class OllamaProcessMixin:
    def start(self) -> None:
        """
        Porneste serverul local Ollama doar daca API-ul nu este deja disponibil.

        In terminal afisam doar mesaje scurte si corecte semantic:
        - mai intai verificam daca API-ul este activ
        - afisam mesajul de pornire doar daca trebuie intr-adevar sa lansam procesul
        """
        if self.is_api_ready():
            self.logger.ai_technical("API-ul Ollama este activ.")
            return

        self.logger.ai_technical("pornesc Ollama...")

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
                self.logger.ai_technical("API-ul Ollama este activ.")
                return
            time.sleep(poll_interval)

        raise RuntimeError("Ollama API nu a devenit disponibila in timp util.")

    def stop(self) -> None:
        """
        Opreste serverul Ollama doar daca a fost pornit de acest framework.
        """
        self.logger.ai_technical("opresc uneltele AI...")

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
        self.logger.ai_technical("resetez contextul.")

    def get_model_name(self) -> str:
        """
        Returneaza numele modelului configurat pentru generare.
        """
        return self.config.ollama.model
