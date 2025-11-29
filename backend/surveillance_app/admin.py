from django.contrib import admin
from .models import (
    SurveillanceArea, Camera, EventType, 
    AreaObservation, ObjectDetail
)

# --- Configuration Models Admin ---

@admin.register(SurveillanceArea)
class SurveillanceAreaAdmin(admin.ModelAdmin):
    """Admin view for managing physical surveillance areas."""
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')

@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    """Admin view for managing individual camera assets."""
    list_display = ('camera_id', 'area', 'is_online', 'ip_address', 'created_at')
    list_filter = ('is_online', 'area')
    search_fields = ('camera_id', 'location_description', 'ip_address')
    # Filter by Area in the admin sidebar for quick searching
    raw_id_fields = ('area',) 

@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    """Admin view for managing the central event types (e.g., WEAPON, CROWD, UOD)."""
    list_display = ('code', 'name', 'priority', 'auto_escalate')
    list_editable = ('priority', 'auto_escalate')
    search_fields = ('code', 'name')
    # Prevent deletion of event types once logs are dependent on them (for safety)
    # Note: EventType.objects.get(code='WEAPON') will be needed for security_app alerts.
    
# --- Transaction/Fact Models Admin ---

class ObjectDetailInline(admin.StackedInline):
    """Inline view for ObjectDetail within AreaObservation."""
    model = ObjectDetail
    can_delete = False # Ensure details are tied to the observation
    verbose_name_plural = 'Observation Details (UOD/Intrusion Metrics)'
    fields = ('object_confidence', 'bounding_box', 'movement_path', 'is_human', 'duration_seconds')

@admin.register(AreaObservation)
class AreaObservationAdmin(admin.ModelAdmin):
    """Admin view for logging non-security critical events (UOD, INTRUSION)."""
    list_display = (
        'id', 'timestamp', 'camera_link', 'event_type', 'status', 'resolution_time'
    )
    list_filter = ('status', 'event_type', 'camera__area')
    search_fields = ('camera__camera_id', 'analyst_notes', 'evidence_path')
    readonly_fields = ('timestamp',)
    inlines = [ObjectDetailInline]

    # Custom display for camera foreign key
    def camera_link(self, obj):
        return f"{obj.camera.camera_id} ({obj.camera.area.name if obj.camera.area else 'N/A'})"
    camera_link.short_description = 'Camera'
    
    # Restrict EventType choices to UOD and INTRUSION as defined in the model's limit_choices_to
    # The default form will handle this automatically based on the model definition.
