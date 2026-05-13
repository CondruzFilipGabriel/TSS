from __future__ import annotations
from pathlib import Path


class AutoRuleScoringMixin:
    def score_rule_candidate(
        self,
        category: str,
        rule: str,
        reasoning: str,
    ) -> int:
        """
        Atribuie un scor euristic unei perechi Rule / Reasoning.

        Scop:
        - nu blocheaza limbajul prin termeni obligatorii
        - foloseste doar semnale moi pentru a compara doua variante valide
        - prefera reguli mai reprezentative, mai generale si mai reconstructive
        """
        normalized_rule = self.normalize_rule_text_for_comparison(rule)
        normalized_reasoning = self.normalize_rule_text_for_comparison(reasoning)

        if not normalized_rule:
            return -100

        score = 0

        if self.is_weak_generic_rule(rule):
            score -= 10
        else:
            score += 3

        word_count = len(normalized_rule.split())
        if 6 <= word_count <= 24:
            score += 2
        elif word_count < 5:
            score -= 2
        elif word_count > 30:
            score -= 1

        causal_markers = [
            "when",
            "if",
            "before",
            "after",
            "instead",
            "because",
            "produces",
            "triggers",
            "causes",
            "leads to",
            "results in",
        ]
        score += min(
            3,
            sum(1 for marker in causal_markers if marker in normalized_rule),
        )

        if category == "functional":
            functional_markers = [
                "observable",
                "outcome",
                "result",
                "validation",
                "exception",
                "boundary",
                "input",
                "behavior",
                "effect",
            ]
            structural_markers = [
                "branch",
                "condition",
                "loop",
                "path",
                "iteration",
                "control flow",
                "execution path",
            ]

            functional_hits = sum(
                1 for marker in functional_markers if marker in normalized_rule
            )
            structural_hits = sum(
                1 for marker in structural_markers if marker in normalized_rule
            )

            score += min(3, functional_hits)

            if structural_hits > functional_hits + 1:
                score -= 2

        elif category == "structural":
            structural_markers = [
                "branch",
                "condition",
                "loop",
                "path",
                "iteration",
                "execution",
                "control flow",
                "validation path",
                "default path",
                "override path",
            ]
            functional_markers = [
                "observable",
                "outcome",
                "result",
                "exception",
                "boundary",
                "input",
            ]

            structural_hits = sum(
                1 for marker in structural_markers if marker in normalized_rule
            )
            functional_hits = sum(
                1 for marker in functional_markers if marker in normalized_rule
            )

            score += min(3, structural_hits)

            if functional_hits > structural_hits + 1:
                score -= 2

        reasoning_markers = [
            "adds",
            "covers",
            "boundary",
            "validation",
            "branch",
            "path",
            "loop",
            "condition",
            "outcome",
            "exception",
        ]
        if any(marker in normalized_reasoning for marker in reasoning_markers):
            score += 1

        return score

    def choose_better_rule_candidate(
        self,
        testing_md_path: Path,
        first_rule: str,
        first_reasoning: str,
        refined_rule: str,
        refined_reasoning: str,
    ) -> tuple[str, str]:
        """
        Alege varianta mai buna dintre prima regula valida si varianta rafinata.

        Regula:
        - daca varianta rafinata are scor mai bun, o pastram pe ea
        - daca scorurile sunt egale, pastram varianta care nu este slaba generic
        - daca si asa sunt egale, pastram prima varianta valida pentru stabilitate
        """
        category = self.workspace.get_category_name_from_testing_md(testing_md_path)

        first_score = self.score_rule_candidate(
            category=category,
            rule=first_rule,
            reasoning=first_reasoning,
        )
        refined_score = self.score_rule_candidate(
            category=category,
            rule=refined_rule,
            reasoning=refined_reasoning,
        )

        if refined_score > first_score:
            return refined_rule, refined_reasoning

        if refined_score == first_score:
            first_is_weak = self.is_weak_generic_rule(first_rule)
            refined_is_weak = self.is_weak_generic_rule(refined_rule)

            if first_is_weak and not refined_is_weak:
                return refined_rule, refined_reasoning

        return first_rule, first_reasoning
