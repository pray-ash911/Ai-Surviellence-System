from django.urls import path
from . import views
# Assuming get_latest_status is defined in views.py, we can typically rely on the 'from . import views'
# But since you explicitly imported it, we'll keep it for clarity.
from .views import get_latest_status 

urlpatterns = [
    # Existing POST endpoint for single frame test
    path('detect/violence/', views.violence_detection_view, name='violence_detection'),
    
    # Existing: GET endpoint for real-time video streaming
    path('video_feed/', views.video_feed_view, name='video_feed'), 

    # CORRECTED PATH: Status API Endpoint now includes /api/
    path('api/latest_status/', get_latest_status, name='latest_status'),
    
    # Home route for basic check
    path('', views.home, name='home'),

    # CORRECTED PATH: Endpoint for fetching logged events now includes /api/
    # This matches the Streamlit request: http://127.0.0.1:8000/api/logs/
    path('api/logs/', views.event_logs_view, name='event_logs'), 
]
