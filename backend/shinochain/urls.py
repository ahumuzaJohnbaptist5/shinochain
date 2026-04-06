from django.contrib import admin
from django.urls import path, include
from accounts.urls import me_urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/", include(me_urlpatterns)),
    path("api/", include("videos.urls")),
    path("api/", include("social.urls")),
    path("api/analytics/", include("analytics.urls")),
]
