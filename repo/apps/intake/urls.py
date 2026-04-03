from django.urls import path

from apps.intake import views

app_name = "intake"

urlpatterns = [
    path("intake/upload", views.upload_page, name="upload-page"),
    path("intake/job-target", views.job_target_page, name="job-target-page"),
    path("api/uploads", views.upload_resume, name="upload-resume"),
    path("api/job-targets", views.create_job_target, name="create-job-target"),
]
