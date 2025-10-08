import cv2
import os
import time
import traceback
import requests 
import urllib.parse 
from django.http import HttpResponse, JsonResponse, StreamingHttpResponse
from rest_framework.decorators import api_view
from rest_framework import status 
from datetime import timedelta
from django.utils import timezone 
from django.utils.timezone import localtime 
from django.conf import settings 
# Required for database logging
from surveillance_app.models import WeaponEvent 

# --- (MODEL IMPORTS AND SETUP ARE OMITTED FOR BREVITY, THEY REMAIN THE SAME) ---

# --- REQUIRED IMPORTS AND MODEL INITIALIZATION ---
try:
    from ultralytics import YOLO 
    print("Ultralytics YOLO imported successfully.")
    
    # --- MODEL 1: WEAPON DETECTION ---
    # Using the file name 'best (1).pt' as provided by the user's working version
    MODEL_FILE_NAME_WEAPON = 'best (1).pt' 
    MODEL_PATH_WEAPON = os.path.join(os.getcwd(), os.pardir, 'models', MODEL_FILE_NAME_WEAPON) 
    WEAPON_MODEL = YOLO(MODEL_PATH_WEAPON) 
    print(f"YOLO (Weapon Detection) Model loaded successfully from: {MODEL_PATH_WEAPON}")


    # --- CONFIGURATION FOR WEAPON DETECTION ---
    INFERENCE_SKIP_FRAMES = 2 
    FIREARM_KEYWORDS = ['gun', 'pistol', 'handgun'] 
    BLADE_KEYWORDS = ['knife', 'sword'] 
    WEAPON_KEYWORDS = FIREARM_KEYWORDS + BLADE_KEYWORDS
    WEAPON_LOG_CONFIDENCE = 0.65 
    LOG_COOLDOWN_SECONDS = 5 

except Exception as e:
    WEAPON_MODEL = None
    print(f"CRITICAL ERROR initializing YOLO model(s): {e}")
    traceback.print_exc()

# --- Utility Function for Home Route ---
def home(request):
    """ Simple Django view for health check. """
    return HttpResponse("<h1>AI Surveillance System Backend is Running (Weapon Detection Core)!</h1>")

# ------------------------------------------------------------------
# 1. GOOGLE FORMS Configuration and Utility (NEW - Replaces IFTTT)
# ------------------------------------------------------------------

# CORRECTED SUBMISSION URL
# We replace '/viewform?usp=header' with '/formResponse'
GOOGLE_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdoEM-r0P7VNPcxbDiXDsvb87s0bX_xTX6_Tuw9XYh2g2YB2w/formResponse" 

# CORRECTED ENTRY IDs
FIELD_ID_IMAGE = "entry.194280707"       # Corresponds to Value1_Image_URL
FIELD_ID_LABEL = "entry.1168214022"      # Corresponds to Value2_Label_Confidence
FIELD_ID_TIME = "entry.1784554534"       # Corresponds to Value3_Timestamp


# This is your active Ngrok URL (e.g., https://febee9fe262e.ngrok-free.app)
# IMPORTANT: Update this whenever your ngrok URL changes.
DJANGO_BASE_URL = "https://883b2c5fbccc.ngrok-free.app" 


def send_google_form_alert(snapshot_relative_path, label, confidence):
    """
    Sends a POST request to Google Forms, triggering a submission 
    and thereby the form's internal email notification.
    """
    # Check if the Ngrok URL has been updated from the placeholder
    if DJANGO_BASE_URL.endswith("YOUR-COPIED-NGROK-URL-HERE"):
        print("WARNING: DJANGO_BASE_URL (Ngrok URL) not updated. Cannot send complete alert.")
        return

    # 1. Construct the public URL for the image.
    safe_path = urllib.parse.quote(snapshot_relative_path)
    # Example: https://febee9fe262e.ngrok-free.app/media/snapshots/file.jpg
    image_url = f"{DJANGO_BASE_URL}{settings.MEDIA_URL}{safe_path}"
    
    # 2. Prepare payload using the specific Google Form entry IDs
    payload = {
        FIELD_ID_IMAGE: image_url, 
        FIELD_ID_LABEL: f"{label} (Conf: {confidence:.2f})", 
        FIELD_ID_TIME: localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S %Z'),
    }
    
    try:
        # Send data to the form response endpoint
        response = requests.post(GOOGLE_FORM_URL, data=payload, timeout=7)
        
        # Google Forms usually returns 200 or 302/303 redirect if successful
        if response.status_code in [200, 302, 303]:
            print(f"Google Forms Alert sent successfully for {label}. Status: {response.status_code}")
        else:
            print(f"Google Forms Alert failed (HTTP {response.status_code}): {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Google Forms Alert failed due to network error: {e}")


# ------------------------------------------------------------------
# 2. SINGLE FRAME DETECTION VIEW (Placeholder)
# ------------------------------------------------------------------
@api_view(['POST'])
def violence_detection_view(request):
    """ 
    DUMMY VIEW: Reintroduced to satisfy existing URL patterns in urls.py.
    This functionality is now handled by the streaming view.
    """
    return JsonResponse({'status': 'info', 'message': 'This endpoint is no longer active. Use /api/video-feed/ for real-time streaming.'}, status=200)

# ------------------------------------------------------------------
# 3. REAL-TIME STREAMING FUNCTIONS (Weapon Detection Core)
# ------------------------------------------------------------------
def generate_frames():
    """ 
    Python generator function that continuously captures and processes 
    frames using the WEAPON_MODEL for real-time weapon detection.
    
    Includes frame skipping for performance.
    """
    # NOTE: (The implementation of generate_frames remains the same, but the 
    # call to send_ifttt_alert is replaced by send_google_form_alert below.)
    
    if WEAPON_MODEL is None:
        print("Weapon Model not available. Exiting stream.")
        return
    
    # 💡 FIX: Explicitly use DirectShow backend for stability on Windows
    # (CAP_DSHOW = 700, the preferred value for reliability on Windows/MSMF issues)
    camera = cv2.VideoCapture(0 + cv2.CAP_DSHOW)
    
    if not camera.isOpened():
        # Check both default (0) and the next index (1) just in case a virtual camera took 0
        camera = cv2.VideoCapture(1 + cv2.CAP_DSHOW)
        if not camera.isOpened():
            print("CRITICAL: Camera is unavailable at index 0 or 1. Stopping stream.")
            return

    last_annotated_frame = None # Stores the last frame annotated by the model
    frame_count = 0
    TARGET_FRAME_TIME_MS = 100 # Target 10 FPS
    
    last_weapon_alert_time = 0
    
    SNAPSHOT_DIR_NAME = 'snapshots' # Folder name relative to MEDIA_ROOT
    
    while True:
        start_time = time.time()
        current_time = time.time()
        success, frame = camera.read()
        
        if not success:
            print("Could not read frame from camera. Stopping stream.")
            break

        current_frame_for_display = frame.copy()
        alert_triggered = False

        frame_count += 1
        # Determine if we run the expensive inference step
        run_inference = (frame_count % (INFERENCE_SKIP_FRAMES + 1)) == 0
        
        # --- Detection and Annotation Logic ---
        try:
            
            if run_inference:
                # --- RUN EXPENSIVE YOLO INFERENCE ---
                results = WEAPON_MODEL.predict(frame, verbose=False, conf=WEAPON_LOG_CONFIDENCE)
            
                # Use the model's built-in plotting to create the annotated frame
                if results and results[0]:
                    last_annotated_frame = results[0].plot()
                else:
                    # If no results and we ran inference, use the raw frame as the last annotated frame
                    last_annotated_frame = current_frame_for_display.copy()
            
            # --- APPLY ANNOTATIONS (Use the last known annotated frame or the current raw frame) ---
            if last_annotated_frame is not None:
                current_frame_for_display = last_annotated_frame.copy()
            
            
            # If any results were returned (for logging checks) AND we ran inference
            if run_inference and results and results[0].boxes:
                
                # Extract relevant information
                confs = results[0].boxes.conf.cpu().numpy()
                classes = results[0].boxes.cls.int().cpu().tolist()
                names = WEAPON_MODEL.names
                
                # Check for any weapon detection
                for conf, cls in zip(confs, classes):
                    
                    class_name = names.get(cls, "unknown").lower()
                    
                    if any(keyword in class_name for keyword in WEAPON_KEYWORDS):
                        
                        # --- STANDARDIZE LABEL FOR LOGGING ---
                        final_weapon_type = "UNKNOWN_WEAPON" 
                        if any(keyword in class_name for keyword in FIREARM_KEYWORDS):
                            final_weapon_type = "FIREARM"
                        elif any(keyword in class_name for keyword in BLADE_KEYWORDS):
                             final_weapon_type = "BLADE"
                             
                        label = f"WEAPON_{final_weapon_type}"
                        
                        # --- LOGGING CHECK: WEAPON DETECTED (Cooldown enforced) ---
                        if current_time - last_weapon_alert_time > LOG_COOLDOWN_SECONDS:
                            
                            # --- FILE PATH HANDLING (Using MEDIA_ROOT logic for persistence) ---
                            # This ensures files are saved to the Django media directory (e.g., /media/snapshots/)
                            SNAPSHOT_FULL_PATH = os.path.join(settings.MEDIA_ROOT, SNAPSHOT_DIR_NAME)
                            os.makedirs(SNAPSHOT_FULL_PATH, exist_ok=True)
                            
                            filename = f"{label}_{int(current_time)}.jpg"
                            filepath = os.path.join(SNAPSHOT_FULL_PATH, filename) # Full path on the server
                            db_snapshot_path = os.path.join(SNAPSHOT_DIR_NAME, filename).replace(os.sep, '/') 
                            
                            # Log the snapshot of the *annotated* frame
                            cv2.imwrite(filepath, current_frame_for_display)
                            
                            # Log to DB using the NEW model name, saving the RELATIVE path
                            WeaponEvent.objects.create(
                                # db_snapshot_path: 'snapshots/WEAPON_FIREARM_123456.jpg'
                                snapshot_path=db_snapshot_path, 
                                confidence=conf,
                                label=label,
                                timestamp=timezone.now()
                            )
                            
                            # --- GOOGLE FORMS ALERT TRIGGER (NEW) ---
                            send_google_form_alert(db_snapshot_path, label, conf)
                            
                            print(f"Logged {label} event: {db_snapshot_path}, Confidence: {conf:.2f}")
                            
                            last_logged_frame = frame_count
                            last_weapon_alert_time = current_time 
                            alert_triggered = True

                        # Overlay primary *system alert message* to confirm logging status
                        cv2.putText(current_frame_for_display, f"!!! {label} DETECTED !!!", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 4)


            # Annotate the display frame if a non-logging alert was recently triggered
            if not alert_triggered and 'last_logged_frame' in locals() and frame_count < last_logged_frame + (INFERENCE_SKIP_FRAMES + 1) * 2: 
                cv2.putText(current_frame_for_display, f"!!! RECENT WEAPON ALERT !!!", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 165, 255), 4)
            
        except Exception as e:
            print(f"YOLO Frame processing error: {e}")
            traceback.print_exc()
            
            # Annotate the display frame to show the error
            cv2.putText(current_frame_for_display, "MODEL ERROR", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 4)

        # --- Encode the processed frame to JPEG ---
        ret, buffer = cv2.imencode('.jpg', current_frame_for_display, [cv2.IMWRITE_JPEG_QUALITY, 70]) 
        if not ret:
            continue
        
        # Yield the frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        
        # Frame Rate Control
        elapsed_time_ms = (time.time() - start_time) * 1000
        wait_time_ms = max(1, int(TARGET_FRAME_TIME_MS - elapsed_time_ms))
        time.sleep(wait_time_ms / 1000)

# Cleanup
    camera.release()

@api_view(['GET'])
def video_feed_view(request):
    """
    This view returns a StreamingHttpResponse that streams the weapon detection feed.
    """
    if WEAPON_MODEL is None:
        return HttpResponse('Weapon Model failed to load.', status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return StreamingHttpResponse(
        generate_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


# ------------------------------------------------------------------
# 4. EVENT LOGS VIEW & STATUS
# ------------------------------------------------------------------
# NOTE: Using placeholder model imports from the original code
try:
    # Assuming WeaponEvent model is correctly defined in surveillance_app/models.py
    from surveillance_app.models import WeaponEvent 
except ImportError:
    # Minimal mock for safety if user hasn't created the model yet (though they should have)
    class WeaponEvent:
        @staticmethod
        def objects():
            return MockManager()
    class MockManager:
        def create(self, **kwargs):
            pass
        def latest(self, *args):
            raise WeaponEvent.DoesNotExist
        def all(self):
            return []
    WeaponEvent.DoesNotExist = type('DoesNotExist', (Exception,), {})
    
# Django views for fetching logs and status...

@api_view(['GET'])
def event_logs_view(request):
    """ Returns a JSON list of all logged events for the dashboard. """
    try:
        # Querying the NEW model name
        events = WeaponEvent.objects.all().order_by('-timestamp')[:100]

        data = []
        for event in events:
            local_timestamp = localtime(event.timestamp)
            
            # --- Generate public snapshot URL for dashboard (NEW) ---
            snapshot_url = None

            # Check if the URL is set to the new or old placeholder
            if DJANGO_BASE_URL != "https://YOUR-COPIED-NGROK-URL-HERE" and DJANGO_BASE_URL != "YOUR_NGROK_OR_PUBLIC_URL_HERE":
                # event.snapshot_path is the relative path (e.g., 'snapshots/WEAPON_FIREARM_16789.jpg')
                safe_path = urllib.parse.quote(event.snapshot_path)
                # snapshot_url will look like: https://your.ngrok.app/media/snapshots/filename.jpg
                snapshot_url = f"{DJANGO_BASE_URL}{settings.MEDIA_URL}{safe_path}"
            # ------------------------------------
            
            data.append({
                'id': event.id,
                'timestamp': local_timestamp.isoformat(), 
                'label': event.label,
                'confidence': event.confidence,
                # Now returning the full public URL instead of the local path
                'snapshot_url': snapshot_url, 
                # Keeping snapshot_path for debugging/compatibility, but it should be replaced by snapshot_url on the frontend
                'snapshot_path': event.snapshot_path
            })

        return JsonResponse(data, safe=False, status=status.HTTP_200_OK)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_latest_status(request):
    """API endpoint for Streamlit to poll for the most recent alert status."""
    try:
        # Querying the NEW model name
        latest_event = WeaponEvent.objects.latest('timestamp')
        alert_window = timedelta(seconds=30)
        is_recent_alert = (timezone.now() - latest_event.timestamp) < alert_window
        local_timestamp = localtime(latest_event.timestamp)

        # Check for any of the monitored alerts
        is_weapon_alert = latest_event.label.upper().startswith('WEAPON_') 
        
        if is_recent_alert and is_weapon_alert: 
            status_data = {
                'status_level': 'ALERT',
                'message': f"!!! {latest_event.label.upper()} DETECTED: at {local_timestamp.strftime('%H:%M:%S')} (Conf: {latest_event.confidence:.2f}) !!!",
                'confidence': latest_event.confidence
            }
        else:
            status_data = {
                'status_level': 'OK',
                'message': 'System operational. Monitoring live stream.',
                'confidence': 0.0
            }
    
    # Using the NEW model name's exception
    except WeaponEvent.DoesNotExist:
        status_data = {
            'status_level': 'IDLE',
            'message': 'System operational. Waiting for first event log.',
            'confidence': 0.0
        }
    except Exception as e:
           status_data = {
             'status_level': 'ERROR',
             'message': f'System Error: {str(e)}',
             'confidence': 0.0
           }
        
    return JsonResponse(status_data, safe=False)
