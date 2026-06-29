"""Skill executor — converts skill calls to tool sequences."""

from typing import Any
from .definitions import get_skill, expand_skill


def skill_to_plan(skill_name: str, user_args: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Convert a skill name to an executable plan. Returns (plan, error)."""
    skill = get_skill(skill_name)
    if skill is None:
        return None, f"Unknown skill: {skill_name}. Available: {list(SKILLS.keys())}"
    try:
        plan = expand_skill(skill, user_args)
        return plan, None
    except Exception as e:
        return None, str(e)


def can_execute_skill(skill_name: str, snapshot: dict[str, Any]) -> tuple[bool, str]:
    """Check if a skill's prerequisites are met. Returns (can_run, reason)."""
    skill = get_skill(skill_name)
    if skill is None:
        return False, f"Unknown skill: {skill_name}"
    for req in skill.requires:
        if not snapshot.get(req, False):
            return False, f"Skill '{skill_name}' requires '{req}' to be True, but it is False."
    return True, ""
