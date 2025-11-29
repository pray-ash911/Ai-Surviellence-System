import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- Configuration ---
LOCAL_URL = "http://127.0.0.1:8000"
ANALYTICS_URL = f"{LOCAL_URL}/api/analytics/"

st.set_page_config(
    page_title="AI Surveillance Analytics Dashboard",
    layout="wide",  # This is good for overall layout
    initial_sidebar_state="expanded"
)

st.title("📊 AI Surveillance Analytics Dashboard")


# Function to fetch analytics data (No Change)
def fetch_analytics_data():
    """Fetches the analytics data from the Django backend."""
    try:
        response = requests.get(ANALYTICS_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data)
        else:
            st.error(f"Failed to fetch analytics data. Status code: {response.status_code}")
            return pd.DataFrame()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to Django API. Server may be down.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching analytics data: {e}")
        return pd.DataFrame()


# Fetch data
analytics_df = fetch_analytics_data()

if not analytics_df.empty:
    # Convert date column to datetime
    analytics_df['date'] = pd.to_datetime(analytics_df['date'])

    ## --- CHANGE 1: Use Radio Buttons for Shorter/Compact Toggle ---
    # Using columns to control the width of the radio selection
    col1, col2 = st.columns([1, 4])
    with col1:
        event_type = st.radio(
            "Select Event Type:",
            options=["Weapon", "Overcrowding"],
            index=0,
            # Key change: Radio buttons are naturally more compact than selectbox
        )

    # Map selection to column
    if event_type == "Weapon":
        y_column = 'weapon'
        color = "#FF0000"  # Red hex
        title = "Weapon Detection Trends (Last 30 Days)"
    else:
        y_column = 'overcrowding'
        color = "#0000FF"  # Blue hex
        title = "Overcrowding Detection Trends (Last 30 Days)"

    # Create line chart
    st.markdown("### Monthly Trend Graph (Last 30 Days)")
    st.subheader(title)
    st.line_chart(
        data=analytics_df.set_index('date')[y_column],
        color=color
    )

    # Display raw data
    with st.expander("View Raw Data"):
        ## --- CHANGE 2: Increase Table Size (Height) ---
        st.dataframe(
            analytics_df,
            height=200  # Set height to 400 pixels to show more rows
        )

else:
    st.warning("No analytics data available. Ensure the Django server is running and events have been logged.")