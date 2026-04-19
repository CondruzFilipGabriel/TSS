import pytest
from to_test import *

def test_classify_hackathon_team_zero_members():
    result = classify_hackathon_team([], 10, False)
    assert result == "no_team"

def test_classify_hackathon_team_negative_hours_left():
    members = [{"skill": 5, "role": "backend", "available": True}]
    hours_left = -1
    has_demo = False

    with pytest.raises(ValueError) as exc_info:
        classify_hackathon_team(members, hours_left, has_demo)

    assert str(exc_info.value) == "hours_left cannot be negative"

# Sfarsitul implementarii testelor initiale existente.

def test_classify_hackathon_team_with_design_member():
    members = [
        {"skill": 5, "role": "backend", "available": True},
        {"skill": 3, "role": "frontend", "available": True},
        {"skill": 4, "role": "design", "available": True}
    ]
    hours_left = 10
    has_demo = False

    result = classify_hackathon_team(members, hours_left, has_demo)

    assert result == "promising"

def test_classify_hackathon_team_with_design_member_and_low_hours_left():
    members = [
        {"skill": 5, "role": "backend", "available": True},
        {"skill": 3, "role": "frontend", "available": True},
        {"skill": 4, "role": "design", "available": True}
    ]
    hours_left = 1
    has_demo = False

    result = classify_hackathon_team(members, hours_left, has_demo)

    assert result == "at_risk"

def test_classify_hackathon_team_with_qa_member():
    members = [
        {"skill": 5, "role": "backend", "available": True},
        {"skill": 3, "role": "frontend", "available": True},
        {"skill": 4, "role": "qa", "available": True}
    ]
    hours_left = 10
    has_demo = False

    result = classify_hackathon_team(members, hours_left, has_demo)

    assert result == "promising"

def test_classify_hackathon_team_with_design_member_and_qa_member():
    members = [
        {"skill": 5, "role": "backend", "available": True},
        {"skill": 3, "role": "frontend", "available": True},
        {"skill": 4, "role": "design", "available": True},
        {"skill": 2, "role": "qa", "available": True}
    ]
    hours_left = 10
    has_demo = False

    result = classify_hackathon_team(members, hours_left, has_demo)

    assert result == "promising"

def test_classify_hackathon_team_with_design_member_and_qa_member_and_no_backend():
    members = [
        {"skill": 5, "role": "frontend", "available": True},
        {"skill": 4, "role": "design", "available": True},
        {"skill": 2, "role": "qa", "available": True}
    ]
    hours_left = 10
    has_demo = False

    result = classify_hackathon_team(members, hours_left, has_demo)

    assert result == "unbalanced"

def test_classify_hackathon_team_with_design_member_and_qa_member_and_no_backend_and_zero_hours_left():
    members = [
        {"skill": 5, "role": "frontend", "available": True},
        {"skill": 4, "role": "design", "available": True},
        {"skill": 2, "role": "qa", "available": True}
    ]
    hours_left = 0
    has_demo = False

    result = classify_hackathon_team(members, hours_left, has_demo)

    assert result == "at_risk"
