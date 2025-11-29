import streamlit as st
import requests
import pandas as pd # <-- Changed to pd for DataFrame handling
import time
import json

# --- CONFIGURATION ---
# IMPORTANT: Replace this with the URL where your Django server is hosted (usually ngrok)
DJANGO_BASE_URL = "http://127.0.0.1:8000" 

# API Endpoints (Checking the provided Django URLs)
# FIX 1: Corrected status URL to include 'latest_' based on common Django endpoint structure.
STATUS_API_URL = f"{DJANGO_BASE_URL}/api/latest_status/"
LOGS_API_URL = f"{DJANGO_BASE_URL}/api/logs/"
# FIX 2: Corrected video feed URL to use an underscore, as is standard in Django paths.
VIDEO_FEED_URL = f"{DJANGO_BASE_URL}/video_feed/"

# --- Polling Intervals (in seconds) ---
STATUS_POLL_INTERVAL = 2
LOGS_POLL_INTERVAL = 5

# --- Page Setup ---
st.set_page_config(layout="wide", page_title="Real-Time AI Surveillance Dashboard")

st.title("🛡️ Real-Time AI Surveillance Dashboard")

# Initialize state for status monitoring and data storage
if 'monitoring_active' not in st.session_state:
    st.session_state.monitoring_active = False
if 'last_status_fetch' not in st.session_state:
    st.session_state.last_status_fetch = 0
if 'last_logs_fetch' not in st.session_state:
    st.session_state.last_logs_fetch = 0
if 'status_data' not in st.session_state:
    st.session_state.status_data = {'status_level': 'IDLE', 'message': 'Monitoring not started.'}
if 'logs_df' not in st.session_state:
    st.session_state.logs_df = pd.DataFrame()
if 'available_labels' not in st.session_state:
    st.session_state.available_labels = ['WEAPON', 'INTRUSION', 'UOD', 'OVERCROWDING']
if 'selected_labels' not in st.session_state:
    st.session_state.selected_labels = st.session_state.available_labels # Select all by default


# --- Functions to Fetch Data ---

def fetch_status():
    """Fetches the latest status from the Django backend."""
    try:
        # Use the corrected STATUS_API_URL
        response = requests.get(STATUS_API_URL, timeout=2)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        # Handle connection errors, timeouts, etc.
        # Log the error to console but return an error status for display
        return {'status_level': 'ERROR', 'message': f'Status fetch failed. Is Django running? ({e})'}

def fetch_logs():
    """Fetches the latest event logs from the Django backend."""
    try:
        response = requests.get(LOGS_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # Format timestamp
        if 'timestamp' in df.columns:
             df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

        # --- CRITICAL FIX: Use snapshot_path to generate local snapshot_url ---
        if 'snapshot_path' in df.columns:
            # Construct the local URL using the base URL and the relative path
            df['snapshot_url_local'] = df['snapshot_path'].apply(lambda x: f"{DJANGO_BASE_URL}/{x}")
            # Drop the original Ngrok URL and rename the new local URL for the table display
            df = df.drop(columns=['snapshot_url'], errors='ignore')
            df.rename(columns={'snapshot_url_local': 'snapshot_url'}, inplace=True)
        # -------------------------------------------------------------------

        # Drop columns not needed for display
        df = df.drop(columns=['id', 'snapshot_path'], errors='ignore')
        
        # Sort by timestamp (newest first)
        return df.sort_values(by='timestamp', ascending=False)
        
    except requests.exceptions.RequestException as e:
        # st.warning("No events logged yet, or API is unavailable.", icon="⚠️")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error processing log data in Streamlit: {e}")
        return pd.DataFrame()


# --- LAYOUT DEFINITION ---
status_col, video_col, logs_col = st.columns([1, 2, 2])

# --- 1. System Status (Left Column) ---
with status_col:
    st.subheader("System Status")
    status_placeholder = st.empty()

# --- 2. Live Video Feed (Center Column) ---
with video_col:
    st.subheader("Live Feed (YOLO Detection)")
    
    # Checkbox to start/stop the video stream
    # Changed from checkbox to button for better start/stop control in polling loop context
    if st.button("Start/Restart System Monitoring"):
        st.session_state.monitoring_active = True
        st.session_state.last_status_fetch = 0
        st.session_state.last_logs_fetch = 0
        st.rerun() 
        
    if not st.session_state.monitoring_active:
        st.warning("Click 'Start/Restart' to activate the video stream and detection.", icon="▶️")


# --- 3. Recent Event Logs (Right Column) ---
with logs_col:
    st.subheader("Recent Event Logs")
    
    # --- ADDED: Filter UI ---
    st.session_state.selected_labels = st.multiselect(
        "Filter by Event Type:",
        options=st.session_state.available_labels,
        default=st.session_state.available_labels,
        placeholder="Select event types..."
    )
    # -----------------------
    
    logs_placeholder = st.empty()


# --- Rendering Function (Moved rendering outside the loop) ---

def render_ui():
    """Renders the dynamic parts of the UI using data from session state."""
    
    # A. Render Status
    status_data = st.session_state.status_data
    level = status_data.get('status_level', 'IDLE')
    message = status_data.get('message', 'Awaiting start.')
            
    with status_placeholder.container():
        if level == 'ALERT':
            st.error(f"🔴 **{level}**\n\n{message}", icon="🚨")
        elif level == 'OK':
            st.success(f"🟢 **{level}**\n\n{message}", icon="✅")
        elif level == 'IDLE':
            st.info(f"🔵 **{level}**\n\n{message}", icon="💤")
        else:
            st.warning(f"🟡 **{level}**\n\n{message}", icon="⚠️")


    # B. Render Video Feed
    with video_col:
        if st.session_state.monitoring_active:
            # MJPEG stream from Django
            st.image(VIDEO_FEED_URL, caption="Real-Time Camera Stream", use_column_width=True)


    # C. Render Event Logs
    logs_df = st.session_state.logs_df
    
    # Apply Filtering
    filtered_df = logs_df
    if not logs_df.empty and st.session_state.selected_labels:
        # Filter the DataFrame based on selected labels
        filtered_df = logs_df[logs_df['label'].isin(st.session_state.selected_labels)]
    
    with logs_placeholder.container():
        if not logs_df.empty:
            if not filtered_df.empty:
                st.dataframe(
                    filtered_df, # Use the filtered DataFrame here
                    column_config={
                        "snapshot_url": st.column_config.LinkColumn(
                            "Snapshot Link", 
                            display_text="View Snapshot",
                            help="Click to open the snapshot image"
                        ),
                        "timestamp": "Timestamp",
                        # Confidence is displayed using the ProgressColumn
                        "confidence": st.column_config.ProgressColumn("Confidence", format="%.2f", min_value=0, max_value=1),
                        "label": "Event Type",
                    },
                    column_order=['timestamp', 'confidence', 'label', 'snapshot_url'], 
                    height=600,
                    hide_index=True
                )
            else:
                st.info("No events match the selected filters.")
        else:
            st.warning("No events logged yet, or API is unavailable.")

# --- Real-Time Monitoring Polling Logic (Non-blocking) ---

if st.session_state.monitoring_active:
    
    current_time = time.time()
    data_changed = False
    
    # 1. Conditional Status Fetch
    if current_time - st.session_state.last_status_fetch >= STATUS_POLL_INTERVAL:
        st.session_state.status_data = fetch_status()
        st.session_state.last_status_fetch = current_time
        data_changed = True
        
    # 2. Conditional Logs Fetch (Less frequent)
    if current_time - st.session_state.last_logs_fetch >= LOGS_POLL_INTERVAL:
        st.session_state.logs_df = fetch_logs()
        st.session_state.last_logs_fetch = current_time
        data_changed = True

    # Render UI if any data was fetched/updated
    if data_changed:
        render_ui()

    # Wait for the shortest interval and force a rerun.
    time.sleep(STATUS_POLL_INTERVAL)
    st.rerun()
else:
    # Initial render when monitoring is inactive
    render_ui()
