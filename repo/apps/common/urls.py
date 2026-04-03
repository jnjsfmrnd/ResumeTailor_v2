from django.urls import path

from apps.common import views

app_name = "common"

urlpatterns = [
    path("", views.home, name="home"),
    path("api/workspace/current", views.current_workspace, name="current-workspace"),
]