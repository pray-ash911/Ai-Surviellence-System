from django.db import models

# --- LOOKUP/CONFIGURATION MODELS ---

class SurveillanceArea(models.Model):
    """
    Defines a physical area being monitored (e.g., Lobby, Warehouse A, Parking Lot).
    """
    name = models.CharField(max_length=100, unique=True, help_text="Human-readable name for the area.")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Camera(models.Model):
    """
    Defines a physical camera asset and its location.
    """
    camera_id = models.CharField(max_length=50, unique=True, help_text="Unique hardware identifier for the camera.")
    area = models.ForeignKey(SurveillanceArea, on_delete=models.SET_NULL, null=True, related_name='cameras')
    location_description = models.CharField(max_length=255, help_text="E.g., 'West wall, facing entrance'.")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    is_online = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Camera {self.camera_id} in {self.area.name if self.area else 'Unassigned'}"

class EventType(models.Model):
    """
    Defines the four distinct categories of events (configuration data).
    This central model is referenced by both security_app and surveillance_app transaction logs.
    """
    EVENT_CHOICES = (
        ('WEAPON', 'Weapon Detection'),
        ('CROWD', 'Overcrowding'),
        ('UOD', 'Unattended Object Detection'),
        ('INTRUSION', 'Suspicious Movement / Intrusion'),
    )

    code = models.CharField(max_length=10, choices=EVENT_CHOICES, unique=True, help_text="Short code for the event type.")
    name = models.CharField(max_length=100, help_text="Full name of the event type.")
    priority = models.IntegerField(default=5, help_text="Priority level (1=High, 10=Low).")
    auto_escalate = models.BooleanField(default=False, help_text="Should this event automatically trigger an alert?")

    def __str__(self):
        return self.name

# --- FACT/TRANSACTION MODELS (AREA/OBJECT DOMAIN) ---

class AreaObservation(models.Model):
    """
    Logs actual UOD and Intrusion/Suspicious Movement events detected by surveillance algorithms.
    This model adheres to the 'Area/Object' domain.
    """
    STATUS_CHOICES = (
        ('NEW', 'New'),
        ('INVESTIGATING', 'Investigating'),
        ('RESOLVED', 'Resolved'),
        ('FALSE_POSITIVE', 'False Positive'),
    )

    timestamp = models.DateTimeField(auto_now_add=True)
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name='area_observations')
    event_type = models.ForeignKey(EventType, on_delete=models.PROTECT, limit_choices_to={'code__in': ['UOD', 'INTRUSION']})
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='NEW')
    analyst_notes = models.TextField(blank=True, null=True)
    resolution_time = models.DateTimeField(null=True, blank=True)
    
    # NEW FIELD: Reference to the image/video file saved in cloud storage for evidence.
    evidence_path = models.CharField(max_length=255, help_text="Path or URL to the digital evidence (snapshot/video clip).")

    def __str__(self):
        return f"{self.event_type.name} at {self.camera.area.name} ({self.timestamp.strftime('%Y-%m-%d %H:%M')})"

class ObjectDetail(models.Model):
    """
    Holds detailed metrics specific to UOD and Suspicious Movement events.
    """
    observation = models.OneToOneField(AreaObservation, on_delete=models.CASCADE, related_name='detail')
    
    # UOD Specific Fields
    object_confidence = models.FloatField(null=True, blank=True, help_text="Confidence score of the UOD detection.")
    bounding_box = models.JSONField(null=True, blank=True, help_text="JSON array for bounding box coordinates [x1, y1, x2, y2].")

    # Intrusion/Suspicious Movement Specific Fields
    movement_path = models.JSONField(null=True, blank=True, help_text="JSON list of coordinates/timestamps for tracking.")
    
    # Common Fields
    is_human = models.BooleanField(default=False)
    duration_seconds = models.IntegerField(default=0, help_text="How long the object was unattended or the movement lasted.")

    def __str__(self):
        return f"Details for {self.observation.id} ({self.observation.event_type.code})"
