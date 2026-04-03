from django.urls import path

from apps.tailoring import gap_review_views

app_name = "tailoring-gaps"

urlpatterns = [
    path(
        "api/tailorings/<str:run_id>/gap-review",
        gap_review_views.gap_review_detail,
        name="gap-review-detail",
    ),
    path(
        "api/tailorings/<str:run_id>/gap-review/refresh",
        gap_review_views.refresh_gap_review,
        name="gap-review-refresh",
    ),
    path(
        "tailoring/<str:run_id>/review/gap-panel",
        gap_review_views.review_gap_panel,
        name="gap-review-panel",
    ),
]
