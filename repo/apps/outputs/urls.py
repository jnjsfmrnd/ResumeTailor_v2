from django.urls import path

from apps.outputs import views

app_name = "outputs"

urlpatterns = [
    path("api/artifacts/resume", views.create_resume_artifact, name="create-resume-artifact"),
    path(
        "api/artifacts/cover-letter",
        views.create_cover_letter_artifact,
        name="create-cover-letter-artifact",
    ),
    path(
        "api/artifacts/<str:artifact_id>/download",
        views.download_artifact,
        name="download-artifact",
    ),
]
