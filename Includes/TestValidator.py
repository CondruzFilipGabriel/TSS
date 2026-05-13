from __future__ import annotations

from Includes.Config import AppConfig
from Includes.Logger import Logger
from Includes.ResponseParser import ParsedResponse, ResponseParser
from Includes.WorkspaceManager import WorkspaceManager
from Includes.validator_static import ValidatorStaticMixin
from Includes.validator_runtime import ValidatorRuntimeMixin
from Includes.validator_core import ValidatorCoreMixin
from Includes.validator_models import ValidationResult


class TestValidator(
    ValidatorStaticMixin,
    ValidatorRuntimeMixin,
    ValidatorCoreMixin,
):
    """Valideaza static si prin pytest o functie de test propusa."""

    def __init__(
        self,
        config: AppConfig,
        logger: Logger,
        workspace: WorkspaceManager,
        response_parser: ResponseParser,
    ) -> None:
        self.config = config
        self.logger = logger
        self.workspace = workspace
        self.response_parser = response_parser


__all__ = ["ValidationResult", "TestValidator"]
