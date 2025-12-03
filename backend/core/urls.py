from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve as static_serve
from django.shortcuts import render

def dashboard_view(request):
    return render(request, 'index.html')

urlpatterns = [
    # Django Administration Site
    path('admin/', admin.site.urls),

    # Frontend dashboard
    path('', dashboard_view, name='dashboard'),

    # API dashboards share
    path('api/', dashboard_view, name='api_dashboard'),

    # 1. Surveillance API Endpoints (FIXED to match AI worker's /api/surveillance/ path)
    # The internal paths in surveillance_app/urls.py must now be relative (e.g., just 'area-observations/')
    path('api/surveillance/', include('backend.surveillance_app.urls')),

    # 2. Security API Endpoints
    # All security-related API calls will start with 'api/security/'.
    path('api/security/', include('backend.security_app.urls')),

    # WebSocket routing
    path('ws/', include('backend.surveillance_app.routing')),
]

# --- Development-Only Configuration ---
if settings.DEBUG:
    # This block is essential for serving media files (like video snapshots) during development.
    urlpatterns += [
        re_path(r'^snapshots/(?P<path>.*)$', static_serve, {
            'document_root': settings.SNAPSHOT_ROOT,
        }),
    ]
