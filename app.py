import streamlit as st
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration
from utils.rep_counter import PushupCounter
import threading


# Page configuration
st.set_page_config(
    page_title="Pushup Rep Counter",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .title {
        text-align: center;
        color: #FF6B6B;
        margin-bottom: 20px;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .instruction {
        background-color: #e8f5e9;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'pushup_counter' not in st.session_state:
    st.session_state.pushup_counter = PushupCounter(
        angle_threshold_down=90,
        angle_threshold_up=150
    )

if 'rep_history' not in st.session_state:
    st.session_state.rep_history = []

# Title
st.markdown('<h1 class="title">💪 Pushup Rep Counter</h1>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    mode = st.radio(
        "Select Mode:",
        ["📹 Live Webcam", "📤 Upload Video"]
    )
    
    st.divider()
    st.subheader("Angle Thresholds")
    angle_down = st.slider(
        "Down Position Angle (°)",
        min_value=40, max_value=120, value=90, step=5,
        help="Elbow angle when in down position"
    )
    angle_up = st.slider(
        "Up Position Angle (°)",
        min_value=130, max_value=180, value=150, step=5,
        help="Elbow angle when in up position"
    )
    
    # Update thresholds
    st.session_state.pushup_counter.angle_threshold_down = angle_down
    st.session_state.pushup_counter.angle_threshold_up = angle_up
    
    st.divider()
    if st.button("🔄 Reset Counter", use_container_width=True):
        st.session_state.pushup_counter.reset()
        st.session_state.rep_history = []
        st.success("Counter reset!")

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    if mode == "📹 Live Webcam":
        st.subheader("Live Webcam Feed")
        
        # Instructions
        st.markdown("""
        <div class="instruction">
        <strong>📋 Instructions:</strong><br>
        1. Position yourself in front of the camera<br>
        2. Ensure your full body is visible<br>
        3. Start doing pushups - the app will count automatically<br>
        4. Keep your elbows in frame for accurate detection
        </div>
        """, unsafe_allow_html=True)
        
        # Webcam capture
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            st.error("❌ Cannot access webcam. Please check permissions.")
        else:
            # Create placeholders
            frame_placeholder = st.empty()
            metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
            
            with metrics_col1:
                rep_count_placeholder = st.empty()
            with metrics_col2:
                angle_placeholder = st.empty()
            with metrics_col3:
                status_placeholder = st.empty()
            
            # Control buttons
            col_start, col_stop = st.columns(2)
            with col_start:
                start_btn = st.button("▶️ Start", use_container_width=True)
            with col_stop:
                stop_btn = st.button("⏹️ Stop", use_container_width=True)
            
            is_running = start_btn
            
            if is_running or st.session_state.get('webcam_running', False):
                st.session_state.webcam_running = True
                
                while st.session_state.webcam_running and not stop_btn:
                    ret, frame = cap.read()
                    if not ret:
                        st.error("Failed to capture frame")
                        break
                    
                    # Flip frame for mirror effect
                    frame = cv2.flip(frame, 1)
                    
                    # Process frame
                    result_frame, rep_count, angle, left_angle, right_angle, status = \
                        st.session_state.pushup_counter.process_frame(frame)
                    
                    # Display frame
                    frame_placeholder.image(
                        cv2.cvtColor(result_frame, cv2.COLOR_BGR2RGB),
                        channels="RGB",
                        use_column_width=True
                    )
                    
                    # Update metrics
                    rep_count_placeholder.metric("Reps Completed", rep_count)
                    angle_placeholder.metric(
                        "Elbow Angle",
                        f"{angle:.1f}°",
                        delta=f"L:{left_angle:.1f}° R:{right_angle:.1f}°"
                    )
                    status_placeholder.metric("Status", status)
        
        cap.release()
    
    else:  # Upload Video mode
        st.subheader("📤 Upload Video")
        
        uploaded_file = st.file_uploader(
            "Upload a video file (MP4, AVI, MOV)",
            type=["mp4", "avi", "mov", "mkv"]
        )
        
        if uploaded_file is not None:
            # Save uploaded file temporarily
            with open("temp_video.mp4", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Process video
            cap = cv2.VideoCapture("temp_video.mp4")
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            st.info(f"📊 Video Info: {frame_count} frames @ {fps} FPS ({duration:.1f}s)")
            
            # Process button
            if st.button("🎬 Process Video", use_container_width=True):
                progress_bar = st.progress(0)
                frame_placeholder = st.empty()
                stats_placeholder = st.empty()
                
                frame_idx = 0
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Resize for faster processing
                    frame = cv2.resize(frame, (640, 480))
                    
                    # Process frame
                    result_frame, rep_count, angle, left_angle, right_angle, status = \
                        st.session_state.pushup_counter.process_frame(frame)
                    
                    # Update display every 5 frames
                    if frame_idx % 5 == 0:
                        frame_placeholder.image(
                            cv2.cvtColor(result_frame, cv2.COLOR_BGR2RGB),
                            channels="RGB",
                            use_column_width=True
                        )
                        
                        stats_placeholder.markdown(f"""
                        **📊 Current Stats:**
                        - Reps: **{rep_count}**
                        - Angle: **{angle:.1f}°**
                        - Status: **{status}**
                        """)
                    
                    # Update progress
                    progress = (frame_idx + 1) / frame_count
                    progress_bar.progress(progress)
                    frame_idx += 1
                
                st.success(f"✅ Video Processing Complete! Total Reps: **{rep_count}**")
            
            cap.release()

# Sidebar statistics
with col2:
    st.subheader("📈 Statistics")
    
    stats = st.session_state.pushup_counter.get_stats()
    
    st.markdown(f"""
    <div class="metric-box">
    <h3>Total Reps: <span style="color: #FF6B6B; font-size: 2em;">{stats['rep_count']}</span></h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="metric-box">
    <p><strong>Current Angle:</strong> {stats['current_angle']:.1f}°</p>
    <p><strong>Status:</strong> {'📍 Down' if stats['is_down'] else '✋ Up'}</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.divider()
st.markdown("""
---
**💡 Tips for Best Results:**
- Ensure good lighting
- Keep your entire body in frame
- Move slowly for accurate angle detection
- Maintain a consistent pushup form
- Get your elbows close to your body

**🔧 Troubleshooting:**
- If reps aren't being counted: Adjust angle thresholds in settings
- If person isn't detected: Check camera angle and lighting
- For video uploads: Use MP4 format for best compatibility
""")
