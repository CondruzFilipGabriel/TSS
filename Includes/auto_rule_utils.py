from __future__ import annotations

from Includes.auto_rule_normalization import AutoRuleNormalizationMixin
from Includes.auto_rule_validation import AutoRuleValidationMixin
from Includes.auto_rule_scoring import AutoRuleScoringMixin


class AutoRuleUtilsMixin(
    AutoRuleNormalizationMixin,
    AutoRuleValidationMixin,
    AutoRuleScoringMixin,
):
    """Grupeaza utilitarele pentru validarea si scorarea regulilor."""

    pass
