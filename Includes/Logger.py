from __future__ import annotations

from Includes.Config import AppConfig
from Includes.logger_files import LoggerFilesMixin
from Includes.logger_rules import LoggerRulesMixin
from Includes.logger_console import LoggerConsoleMixin
from Includes.logger_events import LoggerEventsMixin


class Logger(
    LoggerFilesMixin,
    LoggerRulesMixin,
    LoggerConsoleMixin,
    LoggerEventsMixin,
):
    """Serviciu comun pentru mesaje in consola si loguri persistente."""

    def __init__(
        self,
        config: AppConfig,
        debugging_enabled: bool = False,
        print_debug: bool = True,
    ) -> None:
        self.config = config
        self.debugging_enabled = debugging_enabled
        self.print_debug = print_debug
        self._ensure_debug_directory_exists()
