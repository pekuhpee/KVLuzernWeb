"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from apps.memes import views as meme_views
from config.views import serve_media

urlpatterns = [
    path("", include("apps.pages.urls")),
    path("", include("apps.dyn_dt.urls")),
    path("", include("apps.exams.urls")),
    path("", include("apps.dyn_api.urls")),
    path("ranking/", include("apps.ranking.urls")),
    path("memes/", include("apps.memes.urls")),
    path("admin/", admin.site.urls),
    path("users/", include("apps.users.urls")),
    path("charts/", include("apps.charts.urls")),
    path("tasks/", include("apps.tasks.urls")),
    path("api/memes/", meme_views.api_memes, name="api_memes"),
    path("api/memes/<int:meme_id>/like/", meme_views.api_like_meme, name="api_like_meme"),
    path('api/docs/schema', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/'      , SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path("__debug__/", include("debug_toolbar.urls")),

]

urlpatterns += static(settings.CELERY_LOGS_URL, document_root=settings.CELERY_LOGS_DIR)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif not settings.USE_S3_MEDIA:
    urlpatterns += [path("media/<path:path>", serve_media, name="serve_media")]
