import datetime
from django.contrib import admin
# NOTE: This assumes your models.py now contains the WeaponEvent class
from .models import WeaponEvent 

@admin.register(WeaponEvent)
class WeaponEventAdmin(admin.ModelAdmin):
    """
    Django Admin configuration for the WeaponEvent model.
    Allows easy review and categorization of detection alerts.
    """
    list_display = ('timestamp', 'label', 'confidence', 'status', 'display_time_ago')
    list_filter = ('status', 'label')
    search_fields = ('label', 'snapshot_path')
    actions = ['mark_reviewed', 'mark_false_alarm']

    # Custom display method for time difference
    def display_time_ago(self, obj):
        time_diff = datetime.datetime.now(datetime.timezone.utc) - obj.timestamp
        if time_diff < datetime.timedelta(minutes=1):
            return f"{time_diff.seconds} seconds ago"
        elif time_diff < datetime.timedelta(hours=1):
            minutes = time_diff.seconds // 60
            return f"{minutes} min ago"
        elif time_diff < datetime.timedelta(days=1):
            hours = time_diff.seconds // 3600
            return f"{hours} hours ago"
        else:
            return obj.timestamp.strftime("%Y-%m-%d %H:%M")
    display_time_ago.short_description = "Time Ago"
    
    # Custom actions
    def mark_reviewed(self, request, queryset):
        queryset.update(status='REVIEWED')
    mark_reviewed.short_description = "Mark selected as Reviewed - Valid"

    def mark_false_alarm(self, request, queryset):
        queryset.update(status='FALSE')
    mark_false_alarm.short_description = "Mark selected as False Alarm"
