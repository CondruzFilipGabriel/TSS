import pytest
from to_test import *

def test_classify_hackathon_team_no_members():
    result = classify_hackathon_team([], 10, False)
    assert result == "no_team"

def test_classify_hackathon_team_zero_iterations():
    result = classify_hackathon_team([], 10, False)
    assert result == "no_team"

# Sfarsitul implementarii testelor initiale existente.

def test_classify_hackathon_team_single_member_absent():
    result = classify_hackathon_team([{"skill": 5, "role": "backend", "available": False}], 10, True)
    assert result == "inactive_team"

def test_classify_hackathon_team_single_member_present():
    result = classify_hackathon_team([{"skill": 5, "role": "backend", "available": True}], 10, False)
    assert result == "unbalanced"
