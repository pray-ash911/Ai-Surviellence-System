import streamlit as st
import requests
import pandas as pd
import time
import os
from datetime import datetime
import streamlit as st

# ====== ADD THIS AT THE VERY TOP (after imports) ======
st.markdown("""
<style>
    /* ====== MAIN DARK THEME ====== */
    .stApp {
        background: #0a0e27;
        color: #ffffff;
    }

    /* ====== HEADERS ====== */
    h1, h2, h3 {
        background: linear-gradient(90deg, #0066ff, #00ccff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 1rem;
    }

    /* ====== STATUS BANNERS ====== */
    .stAlert {
        border-radius: 12px;
        border: 1px solid;
        font-weight: bold;
    }

    /* Alert status (weapon detected) */
    div[data-testid="stAlert"]:has(div:contains("🚨")) {
        background: rgba(163, 0, 0, 0.2) !important;
        border-color: #ff3333 !important;
        color: #ff9999 !important;
    }

    /* OK/Idle status */
    div[data-testid="stAlert"]:has(div:contains("✅")) {
        background: rgba(0, 102, 255, 0.2) !important;
        border-color: #0066ff !important;
        color: #99ccff !important;
    }

    /* ====== BUTTONS ====== */
    .stButton > button {
        background: linear-gradient(135deg, #0066ff, #00ccff);
        color: white !important;
        border: none !important;
        border-radius: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.3s ease;
        box-shadow: 0 10px 30px rgba(0, 102, 255, 0.3);
    }

    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 40px rgba(0, 102, 255, 0.4);
    }

    /* ====== DATA TABLE ====== */
    .stDataFrame {
        background: rgba(15, 23, 42, 0.8);
        border: 1px solid rgba(0, 102, 255, 0.3);
        border-radius: 12px;
        color: white;
    }

    /* Table headers */
    .stDataFrame th {
        background: rgba(0, 102, 255, 0.3) !important;
        color: #00ccff !important;
        font-weight: 700;
    }

    /* Table cells */
    .stDataFrame td {
        background: rgba(15, 23, 42, 0.6) !important;
        color: #cbd5e1 !important;
    }

    /* ====== VIDEO FEED CONTAINER ====== */
    .stMarkdown img {
        border-radius: 12px;
        border: 2px solid rgba(0, 102, 255, 0.3);
        box-shadow: 0 0 40px rgba(0, 102, 255, 0.2);
    }

    /* ====== SIDEBAR ====== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0a0e27 0%, #050916 100%);
        border-right: 1px solid rgba(0, 102, 255, 0.3);
    }

    /* ====== METRICS ====== */
    [data-testid="stMetricValue"] {
        color: #00ccff !important;
        font-size: 2rem !important;
        font-weight: 700;
    }

    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* ====== TABS ====== */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(15, 23, 42, 0.8);
        border-radius: 12px;
        padding: 5px;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #94a3b8;
        border-radius: 8px;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0066ff, #00ccff) !important;
        color: white !important;
    }

    /* ====== GRID OVERLAY EFFECT ====== */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: 
            linear-gradient(rgba(0, 102, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 102, 255, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
        z-index: -1;
    }

    /* ====== ANIMATED BACKGROUND ====== */
    .stApp::after {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: 
            radial-gradient(circle at 20% 50%, rgba(0, 102, 255, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 80%, rgba(255, 0, 102, 0.1) 0%, transparent 50%),
            radial-gradient(circle at 40% 20%, rgba(102, 255, 102, 0.05) 0%, transparent 50%);
        animation: bgPulse 10s ease-in-out infinite;
        pointer-events: none;
        z-index: -2;
    }

    @keyframes bgPulse {
        0%, 100% { opacity: 0.5; }
        50% { opacity: 1; }
    }

    /* ====== TEXT ELEMENTS ====== */
    .stText, .stMarkdown, .stSubheader {
        color: #cbd5e1;
    }

    /* ====== PROGRESS BARS ====== */
    .stProgress > div > div {
        background: linear-gradient(90deg, #0066ff, #00ccff);
    }

    /* ====== EXPANDERS ====== */
    .streamlit-expanderHeader {
        background: rgba(0, 102, 255, 0.1);
        border: 1px solid rgba(0, 102, 255, 0.3);
        border-radius: 8px;
        color: #00ccff;
    }

    /* ====== YOUR ANALYTICS BUTTON ====== */
    a button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        width: 100%;
        transition: all 0.3s ease;
        text-decoration: none !important;
    }

    a button:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 30px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)


# --- Configuration (UPDATE) ---
# Local Django server URL for dashboard API calls
LOCAL_URL = "http://127.0.0.1:8000"
# Endpoint for video feed (should be at the app level, e.g., /video_feed/)
VIDEO_FEED_URL = f"{LOCAL_URL}/video_feed/"
# Endpoint for event logs (e.g., /api/logs/) - Updated to match your Django view
LOGS_URL = f"{LOCAL_URL}/api/logs/"
# NEW: Endpoint for the latest status (e.g., /api/latest_status/) - Updated to match your Django view
STATUS_API_URL = f"{LOCAL_URL}/api/latest_status/"

st.set_page_config(
    page_title="AI Surveillance System Dashboard (Weapon & Overcrowding)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Functions to Fetch Data ---

# Function to fetch latest system status
def fetch_system_status():
    """Fetches the latest alert status from the Django backend API."""
    try:
        response = requests.get(STATUS_API_URL, timeout=1) # Use a short timeout
        if response.status_code == 200:
            return response.json()
        else:
            return {'status_level': 'ERROR', 'message': f'Django Status API returned {response.status_code}'}
    except requests.exceptions.ConnectionError:
        return {'status_level': 'ERROR', 'message': 'Cannot connect to Django API. Server may be down.'}
    except requests.exceptions.Timeout:
        return {'status_level': 'ERROR', 'message': 'Django Status API connection timed out.'}
    except Exception as e:
        return {'status_level': 'ERROR', 'message': f'An unknown error occurred: {e}'}

# Function to fetch event logs (Updated for new schema)
def fetch_event_logs():
    """Fetches the latest events (weapon, overcrowding, etc.) from the Django backend."""
    try:
        response = requests.get(LOGS_URL)
        if response.status_code == 200:
            data = response.json()

            # If the response is an empty list, return an empty DataFrame immediately
            if not data:
                return pd.DataFrame()

            df = pd.DataFrame(data)

            # Format datetime
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')

            # Construct display_url locally from snapshot_path for dashboard display
            if 'snapshot_path' in df.columns:
                 df['display_url'] = df['snapshot_path'].apply(
                     lambda p: f"{LOCAL_URL}/snapshots/{p}" if pd.notna(p) and p else None
                 )
            else:
                 # If snapshot_path is not available, set display_url to None
                 df['display_url'] = None

            return df.sort_values(by='timestamp', ascending=False) # Ensure newest is first

        else:
            # Print status code for debugging if the API is returning an error
            st.error(f"Failed to fetch logs. Django Log API returned status code: {response.status_code}")
            return pd.DataFrame()
    except requests.exceptions.ConnectionError:
        # st.error("Cannot connect to Django API for logs.") # Uncomment for deeper debugging
        return pd.DataFrame()
    except Exception as e:
        # Catch unexpected errors during pandas processing
        st.error(f"Error processing log data in Streamlit: {e}")
        return pd.DataFrame()


# --- Dashboard Layout ---

# Navigation Header
# Navigation Header
col_title, col_nav = st.columns([3, 1])
with col_title:
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 15px;">
        <img src="{LOCAL_URL}/static/images/img_4.png" 
             style="width: 130px; height: 130px; border-radius: 10px; 
                    box-shadow: 0 0 15px rgba(0, 102, 255, 0.3); 
                    border: 1px solid rgba(0, 102, 255, 0.2);">
        <h1 style="margin: 0; 
                   font-size: 2.2rem;
                   font-weight: 700;
                   background: linear-gradient(90deg, #0066ff, #00ccff);
                   -webkit-background-clip: text;
                   -webkit-text-fill-color: transparent;
                   background-clip: text;">
            Real-Time AI Surveillance Dashboard
        </h1>
    </div>
    """, unsafe_allow_html=True)

with col_nav:
    st.markdown("<br>", unsafe_allow_html=True)  # Add some spacing
    # Button to navigate to analytics dashboard
    st.markdown("""
    <a href="http://127.0.0.1:8502" target="_self" style="text-decoration: none;">
        <button style="background: linear-gradient(135deg, #0066ff 0%, #00ccff 100%);
                       color: white;
                       border: none;
                       padding: 10px 20px;
                       border-radius: 10px;
                       font-size: 16px;
                       font-weight: 600;
                       cursor: pointer;
                       width: 100%;
                       transition: transform 0.2s;">
            View Analytics Dashboard
        </button>
    </a>
    """, unsafe_allow_html=True)

# 1. Status Banner Placeholder (Top priority)
status_placeholder = st.empty()

# Create two columns for layout
col1, col2 = st.columns([2, 1])

# --- Column 1: Live Video Feed ---
with col1:
    st.header("Live Feed")

    # MJPEG stream from Django
    st.markdown(
        f'<img src="{VIDEO_FEED_URL}" width="100%" style="border-radius: 10px;">',
        unsafe_allow_html=True
    )

# --- Column 2: Event Logs ---
with col2:
    st.header("Recent Event Logs")

    # Event Log Table Placeholder
    log_container = st.empty()


# --- Main Polling Loop for Dynamic Updates ---
if st.button("Start/Restart System Status Monitoring"):
    st.session_state['monitoring_active'] = True

if 'monitoring_active' not in st.session_state:
    st.session_state['monitoring_active'] = False

if st.session_state['monitoring_active']:
    while True:
        # --- A. Update System Status Banner (Polling every 2 seconds) ---
        status_data = fetch_system_status()

        with status_placeholder.container():

            if status_data.get('status_level') == 'ALERT':
                st.markdown(f"""
<div style='background-color: #A30000; color: white; padding: 25px; border-radius: 10px; font-size: 24px; font-weight: bold; text-align: center;'>
    🚨 💥 {status_data['message']} 💥 🚨
</div>
""", unsafe_allow_html=True)

            elif status_data.get('status_level') in ['OK', 'IDLE']:
                st.markdown(f"""
<div style='background-color: #2D4059; color: white; padding: 25px; border-radius: 10px; font-size: 20px; font-weight: bold; text-align: center;'>
    ✅ {status_data['message']}
</div>
""", unsafe_allow_html=True)

            else: # Error case
                st.error(f"⚠️ {status_data['message']}")

        # --- B. Update Event Logs (Polling every 5 seconds) ---
        logs_df = fetch_event_logs()

        with log_container.container():
            if not logs_df.empty:
                # Check if 'display_url' column exists before using it
                if 'display_url' in logs_df.columns:
                    snapshot_url_col = 'display_url'
                else:
                    snapshot_url_col = 'snapshot_path' # Fallback if display_url wasn't created

                st.dataframe(
                    logs_df,
                    column_config={
                        snapshot_url_col: st.column_config.LinkColumn(
                            "Snapshot Link",
                            display_text="View Snapshot",
                            help="Click to open the snapshot image" # Help text can be useful
                        ),
                        "timestamp": "Timestamp",
                        "confidence": st.column_config.ProgressColumn("Confidence", format="%.2f", min_value=0, max_value=1),
                        "label": "Label", # This now comes from event.type.name
                        "snapshot_path": None, # Hide the raw path if we have display_url
                        "id": None, # Optionally hide the internal log ID
                        # Add other columns if needed, e.g., 'area_name' if linked in backend
                    },
                    column_order=['timestamp', 'label', 'confidence', snapshot_url_col], # Reorder as preferred
                    height=600,
                    hide_index=True
                )
            else:
                st.warning("No events logged yet, or API is unavailable.")

        # Sleep for the shorter of the two update intervals
        time.sleep(2) # Polls status every 2 seconds, logs effectively every 5 due to loop and sleep