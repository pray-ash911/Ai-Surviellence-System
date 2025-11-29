from django.http import JsonResponse
from rest_framework import generics
from rest_framework.views import APIView # Needed for the new custom POST view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response # Needed for custom APIView
from rest_framework import status # Needed for custom APIView

from .models import Camera
from .serializers import CameraSerializer, IncidentDisplaySerializer, AreaObservationCreationSerializer # Added AreaObservationCreationSerializer
from backend.security_app.models import SecurityIncident
from .consumers import broadcast_incident_alert

# --- 0. AI WORKER ENDPOINT (NEW) ---

class AreaObservationAPIView(APIView):
    """
    API endpoint for receiving Area Observation events (UOD and INTRUSION)
    from the AI analysis pipeline. These are lower-priority events logged 
    in the surveillance app's database.
    
    NOTE: Authentication is intentionally omitted here as the requests come from 
    a trusted internal service (the AI worker).
    """

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to create a new AreaObservation and its related ObjectDetail.
        """
        serializer = AreaObservationCreationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                # The serializer's create method handles nested ObjectDetail creation
                instance = serializer.save()
                return Response(
                    serializer.to_representation(instance), 
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                print(f"Error during AreaObservation creation: {e}")
                return Response(
                    {"error": "A server error occurred during creation.", "detail": str(e)}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- 1. Camera Management Views ---

class CameraListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for listing all cameras and creating new camera configurations.
    """
    queryset = Camera.objects.all().order_by('area__name', 'camera_id')
    serializer_class = CameraSerializer
    permission_classes = [IsAuthenticated]

class CameraRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for retrieving, updating, or deleting a specific camera configuration.
    """
    queryset = Camera.objects.all()
    serializer_class = CameraSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'id' # Use the Camera ID for lookup

# --- 2. Incident Display Views ---

class RecentIncidentListView(generics.ListAPIView):
    """
    API endpoint to list the most recent security incidents for the dashboard.
    This view reads data from the security_app's model using a read-only serializer.
    """
    # Order by timestamp descending to show the latest incidents first
    queryset = SecurityIncident.objects.all().order_by('-timestamp')
    serializer_class = IncidentDisplaySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Optionally filter the queryset based on parameters (e.g., only unresolved incidents).
        For the dashboard, let's limit it to the 100 most recent items to prevent overload.
        """
        qs = super().get_queryset().filter(is_resolved=False)

        # We can add a filter by priority if needed
        # NOTE: Using 'incident_level' instead of 'priority' based on common security model names
        priority_filter = self.request.query_params.get('priority')
        if priority_filter:
             # Assuming 'incident_level' is the field name on SecurityIncident
            qs = qs.filter(incident_level=priority_filter.upper())

        return qs[:100]

# --- 3. Dashboard View ---

def dashboard_view(request):
    """
    A simple dashboard view that returns a JSON response with basic system status.
    This can be expanded to include more dashboard data.
    """
    return JsonResponse({
        'status': 'Dashboard is operational',
        'message': 'Welcome to the AI Surveillance System Dashboard'
    })

# --- 5. Recent Incidents API for Frontend ---

class RecentIncidentsAPIView(APIView):
    """
    API endpoint to provide recent incidents data for the frontend dashboard.
    Returns incidents in a format suitable for the frontend.
    """
    permission_classes = []  # Allow unauthenticated access for demo

    def get(self, request):
        try:
            # Get recent incidents (last 50)
            incidents = SecurityIncident.objects.all().order_by('-timestamp')[:50]

            incident_data = []
            for incident in incidents:
                # Get confidence score from related metrics or AreaObservation
                confidence_score = None
                snapshot_url = incident.snapshot_url

                # For WEAPON and CROWD incidents, get confidence from metrics
                if hasattr(incident, 'weapon_metrics'):
                    confidence_score = incident.weapon_metrics.confidence
                elif hasattr(incident, 'crowd_metrics'):
                    confidence_score = 0.8  # Default confidence for crowd detection
                # For UOD and INTRUSION, get from AreaObservation
                elif hasattr(incident, 'areaobservation'):
                    area_obs = incident.areaobservation
                    if hasattr(area_obs, 'objectdetail'):
                        confidence_score = area_obs.objectdetail.object_confidence
                    if not snapshot_url:
                        snapshot_url = area_obs.evidence_path

                incident_data.append({
                    'id': incident.id,
                    'event_type': incident.event_type.code,
                    'camera_id': incident.camera.camera_id if incident.camera else 'Unknown',
                    'timestamp': incident.timestamp.isoformat(),
                    'incident_level': incident.incident_level,
                    'confidence_score': confidence_score,
                    'snapshot_url': snapshot_url
                })

            return Response({
                'incidents': incident_data,
                'total_count': len(incident_data)
            })

        except Exception as e:
            return Response(
                {'error': f'Failed to fetch incidents: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# --- 4. Incident Views (for URL patterns) ---

def incident_list_view(request):
    """
    Placeholder for incident list view.
    """
    return JsonResponse({'message': 'Incident list view not implemented yet'})

def incident_detail_view(request, pk):
    """
    Placeholder for incident detail view.
    """
    return JsonResponse({'message': f'Incident detail view for ID {pk} not implemented yet'})
