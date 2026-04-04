from django.urls import path

from apps.common import views
from apps.intake import views as intake_views

app_name = "common"

urlpatterns = [
    path("", intake_views.upload_page, name="home"),
    path("api/workspace/current", views.current_workspace, name="current-workspace"),
]