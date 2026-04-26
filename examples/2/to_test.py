# This function classifies a hackathon team based on its members, remaining time,
# and whether the team already has a demo.
# It first validates the input structure and the global constraints.
# Then it iterates through all team members, validates each member dictionary,
# counts unavailable members, accumulates the skill of available members,
# tracks whether the team has backend and frontend coverage, and counts very low-skill
# available members who may need extra support.
# Finally, it returns the first matching team status in priority order:
# no team, inactive team, time risk, role imbalance, mentoring need, ready,
# promising, or needs scope cut.

def classify_hackathon_team(
    members: list[dict],
    hours_left: int,
    has_demo: bool,
) -> str:
    # Validate that the team data is provided as a list.
    # This is an important test target because non-list inputs must fail immediately.
    if not isinstance(members, list):
        raise TypeError("members must be a list")

    # Validate the remaining time.
    # Negative time is outside the accepted domain and must raise a ValueError.
    if hours_left < 0:
        raise ValueError("hours_left cannot be negative")

    # Handle the empty-team case before any member processing.
    # This branch is important because it returns directly without checking roles or skill.
    if len(members) == 0:
        return "no_team"

    # Initialize counters and flags used while processing the team.
    # These variables are later used to decide the final classification.
    total_skill = 0
    absent_count = 0
    blocked_count = 0
    has_backend = False
    has_frontend = False

    # Process each member, validating structure and accumulating team information.
    # This loop is a major test target because most validation and aggregation logic
    # happens inside it.
    for member in members:
        # Validate that each member is represented as a dictionary.
        if not isinstance(member, dict):
            raise TypeError("each member must be a dict")

        # Validate that all required fields are present.
        # Missing fields make the member data incomplete and must stop processing.
        if "skill" not in member or "role" not in member or "available" not in member:
            raise ValueError("member is missing required fields")

        # Extract the member fields after the required-field check.
        skill = member["skill"]
        role = member["role"]
        available = member["available"]

        # Validate field types.
        # `skill` must be an integer and `available` must be a boolean.
        if not isinstance(skill, int) or not isinstance(available, bool):
            raise TypeError("invalid member field type")

        # Validate the accepted skill range.
        # Boundary values 0 and 10 are valid, while values outside this interval are invalid.
        if skill < 0 or skill > 10:
            raise ValueError("skill out of range")

        # Validate the member role against the allowed role set.
        if role not in {"backend", "frontend", "design", "qa"}:
            raise ValueError("invalid role")

        # Count unavailable members and skip their skill and role contribution.
        # The `continue` is important because absent members do not affect total skill,
        # role coverage, or blocked-member counting.
        if not available:
            absent_count += 1
            continue

        # Add the skill of available members only.
        total_skill += skill

        # Track whether the available team has backend coverage.
        if role == "backend":
            has_backend = True

        # Track whether the available team has frontend coverage.
        if role == "frontend":
            has_frontend = True

        # Count available members with very low skill as blocked members.
        # This branch affects the mentoring-needed classification.
        if skill <= 2:
            blocked_count += 1

    # If all listed members are unavailable, the team is inactive.
    # This classification has priority over demo, balance, skill, and scope checks.
    if absent_count == len(members):
        return "inactive_team"

    # If there is no demo and very little time remains, the team is at risk.
    # This branch has priority over role balance and skill-based classifications.
    if not has_demo and hours_left <= 2:
        return "at_risk"

    # A team without available backend or frontend coverage is unbalanced.
    # This check uses only available members because absent members were skipped above.
    if not has_backend or not has_frontend:
        return "unbalanced"

    # If at least two available members are blocked, the team needs mentoring.
    if blocked_count >= 2:
        return "mentoring_needed"

    # A high-skill team with a demo is ready.
    # This is the strongest positive classification.
    if total_skill >= 20 and has_demo:
        return "ready"

    # A team with enough available skill, but not enough to be ready, is promising.
    if total_skill >= 12:
        return "promising"

    # If no previous condition matched, the team should reduce its scope.
    return "needs_scope_cut"