from __future__ import annotations

from apps.tailoring.gap_service import analyze_skill_gaps


def test_analyze_skill_gaps_classifies_missing_requirements() -> None:
    job_description = (
        "Need Django, Terraform, and Kubernetes experience with CI/CD ownership."
    )
    resume_text = "Built Django APIs and owned CI pipelines with infrastructure automation."

    result = analyze_skill_gaps(job_description=job_description, resume_text=resume_text)

    missing = {item["requirement"]: item for item in result["missing_requirements"]}
    assert "kubernetes" in missing
    assert missing["kubernetes"]["classification"] == "unsupported"
    assert "terraform" in missing
    assert missing["terraform"]["classification"] == "partially_transferable"


def test_analyze_skill_gaps_returns_transferable_skill_mappings() -> None:
    job_description = "Looking for Terraform and event-driven systems expertise."
    resume_text = "Implemented infrastructure automation and event-driven data workflows."

    result = analyze_skill_gaps(job_description=job_description, resume_text=resume_text)

    mappings = result["transferable_skills"]
    assert any(m["target"] == "terraform" for m in mappings)
    assert any("infrastructure automation" in m["evidence"] for m in mappings)


def test_analyze_skill_gaps_handles_empty_inputs() -> None:
    result = analyze_skill_gaps(job_description="", resume_text="")

    assert result["missing_requirements"] == []
    assert result["transferable_skills"] == []
    assert "insufficient" in result["coverage_summary"].lower()
