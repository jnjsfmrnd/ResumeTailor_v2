from __future__ import annotations

import json

import pytest
from django.test import Client

from apps.common.models import WorkspaceSession
from apps.intake.models import JobTarget, SourceDocument
from apps.tailoring.models import (
    ProjectBulletProposal,
    ProjectRecommendation,
    SkillGapAssessment,
    TailoringRun,
)

pytestmark = pytest.mark.contract


@pytest.fixture(autouse=True)
def _use_gap_review_urlconf(settings):
    settings.ROOT_URLCONF = "apps.tailoring.gap_review_urls"


@pytest.fixture
def reviewable_run(client, db):
    session = client.session
    session.save()
    ws = WorkspaceSession.objects.create(session_key=session.session_key)
    doc = SourceDocument.objects.create(
        workspace_session=ws,
        original_filename="resume.pdf",
        content_type=SourceDocument.ContentType.PDF,
        blob_path="resume/resume.pdf",
        sha256="a" * 64,
        extracted_text="Django API development and infrastructure automation.",
        parse_status=SourceDocument.ParseStatus.READY,
        is_current=True,
    )
    target = JobTarget.objects.create(
        workspace_session=ws,
        role_title="Platform Engineer",
        description_text="Need Kubernetes and Terraform experience.",
    )
    run = TailoringRun.objects.create(
        workspace_session=ws,
        source_document=doc,
        job_target=target,
        status=TailoringRun.Status.REVIEWABLE,
        professional_summary="Platform-focused backend engineer.",
        tailored_skills=["Django", "Python"],
        tailored_experience_sections=[{"role": "Engineer"}],
    )

    SkillGapAssessment.objects.create(
        tailoring_run=run,
        missing_requirements=[
            {"requirement": "kubernetes", "classification": "unsupported"}
        ],
        transferable_skills=[
            {
                "target": "terraform",
                "source": "infrastructure automation",
                "evidence": "Built infra automation scripts.",
            }
        ],
        coverage_summary="Strong backend alignment with one infrastructure gap.",
    )
    recommendation = ProjectRecommendation.objects.create(
        tailoring_run=run,
        title="Build a Kubernetes deployment accelerator",
        goal="Close practical deployment experience gap.",
        scope_markdown="## Scope\n- Build deployment templates",
        targeted_gaps=["kubernetes", "terraform"],
        is_included=False,
    )
    ProjectBulletProposal.objects.create(
        project_recommendation=recommendation,
        sort_order=1,
        generated_text="Built deployment pipelines for containerized services.",
    )
    return run


def test_get_tailoring_review_detail_includes_gap_payload(client, reviewable_run):
    response = client.get(f"/api/tailorings/{reviewable_run.id}/gap-review")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(reviewable_run.id)
    assert "skillGapAssessment" in payload
    assert "projectRecommendations" in payload
    assert payload["projectRecommendations"][0]["targetedGaps"] == ["kubernetes", "terraform"]


def test_patch_tailoring_review_updates_include_exclude_choices(client, reviewable_run):
    recommendation = reviewable_run.project_recommendations.first()
    bullet = recommendation.bullets.first()

    response = client.patch(
        f"/api/tailorings/{reviewable_run.id}/gap-review",
        data=json.dumps(
            {
                "projectRecommendations": [
                    {
                        "id": str(recommendation.id),
                        "isIncluded": True,
                        "bullets": [
                            {
                                "id": str(bullet.id),
                                "editedText": "Implemented Kubernetes-ready deployment pipelines.",
                                "isApproved": True,
                            }
                        ],
                    }
                ]
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 200
    recommendation.refresh_from_db()
    bullet.refresh_from_db()
    assert recommendation.is_included is True
    assert bullet.is_approved is True
    assert bullet.edited_text == "Implemented Kubernetes-ready deployment pipelines."


def test_patch_tailoring_review_rejects_invalid_payload(client, reviewable_run):
    response = client.patch(
        f"/api/tailorings/{reviewable_run.id}/gap-review",
        data=json.dumps({"projectRecommendations": "not-a-list"}),
        content_type="application/json",
    )

    assert response.status_code == 400


def test_gap_review_returns_404_for_another_workspace(reviewable_run):
    from django.test import Client

    other_client = Client()

    response = other_client.get(f"/api/tailorings/{reviewable_run.id}/gap-review")

    assert response.status_code == 404


def test_gap_review_patch_returns_404_for_another_workspace(reviewable_run):
    other_client = Client()
    recommendation = reviewable_run.project_recommendations.first()
    bullet = recommendation.bullets.first()

    response = other_client.patch(
        f"/api/tailorings/{reviewable_run.id}/gap-review",
        data=json.dumps(
            {
                "projectRecommendations": [
                    {
                        "id": str(recommendation.id),
                        "isIncluded": True,
                        "bullets": [
                            {
                                "id": str(bullet.id),
                                "editedText": "Should not apply.",
                                "isApproved": True,
                            }
                        ],
                    }
                ]
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 404


def test_gap_review_patch_rejects_missing_csrf_token(reviewable_run):
    client = Client(enforce_csrf_checks=True)
    token = "b" * 32
    client.cookies["csrftoken"] = token
    recommendation = reviewable_run.project_recommendations.first()
    bullet = recommendation.bullets.first()

    response = client.patch(
        f"/api/tailorings/{reviewable_run.id}/gap-review",
        data=json.dumps(
            {
                "projectRecommendations": [
                    {
                        "id": str(recommendation.id),
                        "isIncluded": True,
                        "bullets": [
                            {
                                "id": str(bullet.id),
                                "editedText": "Blocked.",
                                "isApproved": True,
                            }
                        ],
                    }
                ]
            }
        ),
        content_type="application/json",
    )

    assert response.status_code == 403
