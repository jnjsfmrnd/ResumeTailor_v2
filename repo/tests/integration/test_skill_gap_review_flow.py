from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from django.test import Client

from apps.common.models import WorkspaceSession
from apps.intake.models import JobTarget, SourceDocument
from apps.tailoring.models import TailoringRun

pytestmark = pytest.mark.integration


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
        sha256="b" * 64,
        extracted_text="Django APIs, Python services, and CI automation.",
        parse_status=SourceDocument.ParseStatus.READY,
        is_current=True,
    )
    target = JobTarget.objects.create(
        workspace_session=ws,
        role_title="Platform Engineer",
        description_text=(
            "Need Terraform and Kubernetes delivery experience with production observability."
        ),
    )
    return TailoringRun.objects.create(
        workspace_session=ws,
        source_document=doc,
        job_target=target,
        status=TailoringRun.Status.REVIEWABLE,
        professional_summary="Backend engineer focused on platform reliability.",
        tailored_skills=["Python", "Django"],
        tailored_experience_sections=[{"role": "Engineer"}],
    )


def test_gap_flow_supports_empty_refresh_and_inclusion_decisions(client, reviewable_run):
    empty_response = client.get(f"/api/tailorings/{reviewable_run.id}/gap-review")
    assert empty_response.status_code == 200
    assert empty_response.json()["projectRecommendations"] == []

    refresh_response = client.post(f"/api/tailorings/{reviewable_run.id}/gap-review/refresh")
    assert refresh_response.status_code == 200

    refreshed = refresh_response.json()
    assert len(refreshed["projectRecommendations"]) == 1
    recommendation = refreshed["projectRecommendations"][0]
    bullet = recommendation["bullets"][0]

    update_response = client.patch(
        f"/api/tailorings/{reviewable_run.id}/gap-review",
        data=json.dumps(
            {
                "projectRecommendations": [
                    {
                        "id": recommendation["id"],
                        "isIncluded": True,
                        "bullets": [
                            {
                                "id": bullet["id"],
                                "editedText": (
                                    "Built Terraform modules and Kubernetes rollout"
                                    " automation for staging clusters."
                                ),
                                "isApproved": True,
                            }
                        ],
                    }
                ]
            }
        ),
        content_type="application/json",
    )
    assert update_response.status_code == 200
    updated_payload = update_response.json()
    assert updated_payload["projectRecommendations"][0]["isIncluded"] is True
    assert updated_payload["projectRecommendations"][0]["bullets"][0]["isApproved"] is True


def test_gap_review_validation_and_error_states(client, reviewable_run):
    bad_response = client.patch(
        f"/api/tailorings/{reviewable_run.id}/gap-review",
        data=json.dumps({"projectRecommendations": {}}),
        content_type="application/json",
    )
    assert bad_response.status_code == 400

    with patch(
        "apps.tailoring.gap_review_views.refresh_gap_intelligence",
        side_effect=RuntimeError("gap analysis unavailable"),
    ):
        error_response = client.post(f"/api/tailorings/{reviewable_run.id}/gap-review/refresh")

    assert error_response.status_code == 502
    assert "error" in error_response.json()


def test_gap_review_refresh_records_latency_metric(client, reviewable_run):
    with patch("apps.tailoring.gap_review_views.record_latency") as record_latency_mock:
        response = client.post(f"/api/tailorings/{reviewable_run.id}/gap-review/refresh")

    assert response.status_code == 200
    record_latency_mock.assert_called_once()


def test_gap_review_refresh_returns_404_for_another_workspace(reviewable_run):
    other_client = Client()

    response = other_client.post(f"/api/tailorings/{reviewable_run.id}/gap-review/refresh")

    assert response.status_code == 404
