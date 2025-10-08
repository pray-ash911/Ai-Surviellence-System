# backend/surveillance_app/models.py
from django.db import models

class WeaponEvent(models.Model):
    STATUS_CHOICES = [
        ('NEW', 'New'),
        ('REVIEWED', 'Reviewed - Valid'),
        ('FALSE', 'False Alarm'),
    ]
    # Field to store the path or name of the image snapshot
    # Adjust max_length based on expected path length
    snapshot_path = models.CharField(max_length=255, help_text="Path to the saved snapshot image.")
    
    # Timestamp of when the event occurred
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Optional: Confidence score of the detection
    confidence = models.FloatField(null=True, blank=True)
    
    # Optional: Type of violence detected (e.g., 'fight', 'punch', 'kick')
    label = models.CharField(max_length=50, default='')

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='NEW')

    def __str__(self):
        return f"Violence Event at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

   