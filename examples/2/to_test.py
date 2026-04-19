def classify_hackathon_team(
    members: list[dict],
    hours_left: int,
    has_demo: bool,
) -> str:
    if not isinstance(members, list):
        raise TypeError("members must be a list")

    if hours_left < 0:
        raise ValueError("hours_left cannot be negative")

    if len(members) == 0:
        return "no_team"

    total_skill = 0
    absent_count = 0
    blocked_count = 0
    has_backend = False
    has_frontend = False

    for member in members:
        if not isinstance(member, dict):
            raise TypeError("each member must be a dict")

        if "skill" not in member or "role" not in member or "available" not in member:
            raise ValueError("member is missing required fields")

        skill = member["skill"]
        role = member["role"]
        available = member["available"]

        if not isinstance(skill, int) or not isinstance(available, bool):
            raise TypeError("invalid member field type")

        if skill < 0 or skill > 10:
            raise ValueError("skill out of range")

        if role not in {"backend", "frontend", "design", "qa"}:
            raise ValueError("invalid role")

        if not available:
            absent_count += 1
            continue

        total_skill += skill

        if role == "backend":
            has_backend = True
        if role == "frontend":
            has_frontend = True

        if skill <= 2:
            blocked_count += 1

    if absent_count == len(members):
        return "inactive_team"

    if not has_demo and hours_left <= 2:
        return "at_risk"

    if not has_backend or not has_frontend:
        return "unbalanced"

    if blocked_count >= 2:
        return "mentoring_needed"

    if total_skill >= 20 and has_demo:
        return "ready"

    if total_skill >= 12:
        return "promising"

    return "needs_scope_cut"