from django.urls import path

from apps.tailoring import review_views

app_name = "tailoring"

urlpatterns = [
    # JSON API endpoints
    path("api/tailorings", review_views.start_tailoring_run, name="start-run"),
    path(
        "api/tailorings/<str:run_id>",
        review_views.tailoring_run_detail,
        name="run-detail",
    ),
    # HTML review page
    path(
        "tailoring/<str:run_id>/review",
        review_views.review_page,
        name="review-page",
    ),
]
