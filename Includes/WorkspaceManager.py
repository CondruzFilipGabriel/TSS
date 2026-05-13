from __future__ import annotations

from Includes.Config import AppConfig
from Includes.Logger import Logger
from Includes.workspace_io import WorkspaceIOMixin
from Includes.workspace_tests import WorkspaceTestsMixin
from Includes.workspace_rules import WorkspaceRulesMixin


class WorkspaceManager(
    WorkspaceIOMixin,
    WorkspaceTestsMixin,
    WorkspaceRulesMixin,
):
    """Gestioneaza fisierele si folderele proiectului de testare."""

    def __init__(self, config: AppConfig, logger: Logger) -> None:
        self.config = config
        self.logger = logger
