from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as static_serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('surveillance_app.urls')), 
]

if settings.DEBUG:
    # serve files from settings.SNAPSHOT_ROOT at /snapshots/... (development only)
    urlpatterns += [
        re_path(r'^snapshots/(?P<path>.*)$', static_serve, {
            'document_root': settings.SNAPSHOT_ROOT,
        }),
    ]
