from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.common.urls")),
    path("", include("apps.intake.urls")),
    path("", include("apps.outputs.urls")),
    path("", include("apps.tailoring.review_urls")),
]

handler400 = "apps.common.views.bad_request"
handler404 = "apps.common.views.not_found"
handler500 = "apps.common.views.server_error"