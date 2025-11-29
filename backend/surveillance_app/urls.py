from django.urls import path
from . import views
from .views import (
    CameraListCreateView,
    CameraRetrieveUpdateDestroyView,
    RecentIncidentListView,
    AreaObservationAPIView,
    RecentIncidentsAPIView
)

# Set app_name for namespacing
app_name = 'surveillance_app'

urlpatterns = [
    # --- 1. AI Data Ingestion Endpoints (Corrected: Removed redundant 'api/') ---
    # Full URL: /api/surveillance/area-observations/
    path(
        'area-observations/', 
        AreaObservationAPIView.as_view(), 
        name='area-observation-api'
    ),

    # --- 2. Dashboard & Reporting Data Endpoints (Corrected: Removed redundant 'api/') ---
    # Full URL: /api/surveillance/recent-incidents/
    path(
        'recent-incidents/', 
        RecentIncidentListView.as_view(), 
        name='recent-incident-list'
    ),

    # Frontend API endpoint for recent incidents
    path(
        'recent-incidents-frontend/',
        RecentIncidentsAPIView.as_view(),
        name='recent-incidents-frontend'
    ),

    # --- 3. Camera Management Endpoints (Corrected: Removed redundant 'api/') ---
    # Full URL: /api/surveillance/cameras/
    path(
        'cameras/', 
        CameraListCreateView.as_view(), 
        name='camera-list-create'
    ),
    # Full URL: /api/surveillance/cameras/<int:pk>/
    path(
        'cameras/<int:pk>/', 
        CameraRetrieveUpdateDestroyView.as_view(), 
        name='camera-detail-update-delete'
    ),
    
    # --- 4. Placeholder & Legacy Views ---
    # These paths are correctly defined relative to /api/surveillance/ (e.g., /api/surveillance/incidents/)
    
    # Main Dashboard View
    path('', views.dashboard_view, name='dashboard'), 
    
    # Incident List View
    path('incidents/', views.incident_list_view, name='incident-list'),
    
    # Incident Detail View
    path('incidents/<int:pk>/', views.incident_detail_view, name='incident-detail'),

]
