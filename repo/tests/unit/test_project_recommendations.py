from __future__ import annotations

from apps.tailoring.gap_service import build_project_recommendation


def test_build_project_recommendation_outputs_required_fields() -> None:
    recommendation = build_project_recommendation(
        role_title="Platform Engineer",
        missing_requirements=[
            {"requirement": "kubernetes", "classification": "unsupported"},
            {"requirement": "terraform", "classification": "partially_transferable"},
        ],
        transferable_skills=[
            {
                "target": "terraform",
                "source": "infrastructure automation",
                "evidence": "Built infrastructure automation for internal services.",
            }
        ],
    )

    assert recommendation["title"]
    assert recommendation["goal"]
    assert recommendation["scope_markdown"].startswith("##")
    assert recommendation["targeted_gaps"] == ["kubernetes", "terraform"]
    assert len(recommendation["bullets"]) >= 3


def test_build_project_recommendation_bullets_are_resume_ready() -> None:
    recommendation = build_project_recommendation(
        role_title="Backend Engineer",
        missing_requirements=[{"requirement": "redis", "classification": "unsupported"}],
        transferable_skills=[],
    )

    bullets = recommendation["bullets"]
    assert all(bullet.endswith(".") for bullet in bullets)
    assert any("Implemented" in bullet or "Built" in bullet for bullet in bullets)


def test_build_project_recommendation_handles_no_gaps() -> None:
    recommendation = build_project_recommendation(
        role_title="Engineer",
        missing_requirements=[],
        transferable_skills=[],
    )

    assert recommendation["targeted_gaps"] == []
    assert "portfolio" in recommendation["goal"].lower()
