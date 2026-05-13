from __future__ import annotations

from Includes.Config import AppConfig
from Includes.Logger import Logger
from Includes.WorkspaceManager import WorkspaceManager
from Includes.performance_commands import PerformanceCommandsMixin
from Includes.performance_pytest_coverage import PerformancePytestCoverageMixin
from Includes.performance_mutation import PerformanceMutationMixin
from Includes.performance_scoring import PerformanceScoringMixin
from Includes.performance_models import PerformanceScores


class TestsPerformance(
    PerformanceCommandsMixin,
    PerformancePytestCoverageMixin,
    PerformanceMutationMixin,
    PerformanceScoringMixin,
):
    """Coordoneaza masurarea pytest, coverage si mutation score."""

    def __init__(
        self,
        config: AppConfig,
        logger: Logger,
        workspace: WorkspaceManager,
    ) -> None:
        self.config = config
        self.logger = logger
        self.workspace = workspace


__all__ = ["PerformanceScores", "TestsPerformance"]
