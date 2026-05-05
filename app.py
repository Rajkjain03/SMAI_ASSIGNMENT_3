import streamlit as st
import cv2
import av
from streamlit_webrtc import WebRtcMode, RTCConfiguration, webrtc_streamer
from utils.rep_counter import PushupCounter
import os
import tempfile
import time


# Page configuration
st.set_page_config(
    page_title="Pushup Rep Counter",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)


def open_camera_capture(preferred_index: int = 0):
    """Open a webcam capture robustly by trying multiple indices/backends."""
    candidate_indices = [preferred_index] + [idx for idx in [0, 1, 2] if idx != preferred_index]

    for idx in candidate_indices:
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(idx)

        if cap.isOpened():
            return cap, idx

        cap.release()

    return None, None


def release_opencv_camera():
    """Release persistent OpenCV camera handle, if present."""
    cap = st.session_state.get("opencv_cap")
    if cap is not None:
        cap.release()
    st.session_state.opencv_cap = None
    st.session_state.active_camera_index = None

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

if 'last_frame_metrics' not in st.session_state:
    st.session_state.last_frame_metrics = {
        "rep_count": 0,
        "angle": 0.0,
        "left_angle": 0.0,
        "right_angle": 0.0,
        "status": "Waiting"
    }

if 'opencv_fallback_running' not in st.session_state:
    st.session_state.opencv_fallback_running = False

if 'preferred_camera_index' not in st.session_state:
    st.session_state.preferred_camera_index = 0

if 'opencv_cap' not in st.session_state:
    st.session_state.opencv_cap = None

if 'active_camera_index' not in st.session_state:
    st.session_state.active_camera_index = None

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
    st.subheader("📷 Camera Device")
    st.session_state.preferred_camera_index = st.selectbox(
        "Preferred Camera Index",
        options=[0, 1, 2],
        index=st.session_state.preferred_camera_index,
        help="If one index does not work, choose another."
    )

    st.divider()
    if st.button("🔄 Reset Counter", use_container_width=True):
        st.session_state.pushup_counter.reset()
        st.session_state.rep_history = []
        st.success("Counter reset!")

# Main content
col1, col2 = st.columns([3, 1])

with col1:
    if mode == "📹 Live Webcam":
        st.subheader("📹 Live Webcam Feed")

        camera_backend = st.radio(
            "Camera Backend",
            ["OpenCV Fallback (recommended)", "WebRTC (experimental)"],
            index=0,
            horizontal=True,
            help="OpenCV fallback is more reliable on local Linux machines."
        )

        with st.expander("🛠️ Camera not starting? Try this", expanded=True):
            st.markdown(
                """
                If START keeps loading, this is usually a browser/WebRTC issue.

                1. Open the app using **http://localhost:8501** (not Network/External URL)
                2. Use Chrome/Edge and allow camera permission
                3. Close other apps using webcam (Zoom/Meet/Teams)
                4. Reload once after granting permission
                """
            )

            if st.button("🔍 Test Local Camera (OpenCV)", use_container_width=True):
                test_cap, active_index = open_camera_capture(st.session_state.preferred_camera_index)
                ok = False
                test_frame = None
                if test_cap is not None:
                    ok, test_frame = test_cap.read()
                    test_cap.release()

                if ok:
                    st.success(
                        f"Camera works in Python (device index {active_index}). If WebRTC still loads forever, use OpenCV fallback mode."
                    )
                    st.image(
                        cv2.cvtColor(test_frame, cv2.COLOR_BGR2RGB),
                        channels="RGB",
                        caption="OpenCV camera test frame",
                        use_column_width=True,
                    )
                else:
                    st.error(
                        "Python cannot access webcam (device busy or permission denied). Close other camera apps and retry."
                    )
        
        # Instructions
        st.markdown("""
        <div class="instruction">
        <strong>📋 Instructions:</strong><br>
        1. Select webcam backend above<br>
        2. Position yourself in front of the camera<br>
        3. Ensure your upper body and elbows are visible<br>
        4. Do pushups continuously for automatic counting<br>
        5. Stop webcam when finished
        </div>
        """, unsafe_allow_html=True)

        webrtc_ctx = None
        if camera_backend == "WebRTC (experimental)":
            if st.session_state.opencv_fallback_running or st.session_state.opencv_cap is not None:
                st.session_state.opencv_fallback_running = False
                release_opencv_camera()

            def video_frame_callback(frame):
                image = frame.to_ndarray(format="bgr24")
                image = cv2.flip(image, 1)
                result_frame, rep_count, angle, left_angle, right_angle, status = \
                    st.session_state.pushup_counter.process_frame(image)

                st.session_state.last_frame_metrics = {
                    "rep_count": rep_count,
                    "angle": angle,
                    "left_angle": left_angle,
                    "right_angle": right_angle,
                    "status": status,
                }

                return av.VideoFrame.from_ndarray(result_frame, format="bgr24")

            webrtc_ctx = webrtc_streamer(
                key="pushup-live-stream",
                mode=WebRtcMode.SENDRECV,
                rtc_configuration=RTC_CONFIGURATION,
                media_stream_constraints={"video": True, "audio": False},
                video_frame_callback=video_frame_callback,
                async_processing=True,
            )
        else:
            col_start, col_stop = st.columns(2)
            with col_start:
                if st.button("▶️ Start OpenCV Camera", use_container_width=True):
                    st.session_state.opencv_fallback_running = True
                    release_opencv_camera()
            with col_stop:
                if st.button("⏹️ Stop OpenCV Camera", use_container_width=True):
                    st.session_state.opencv_fallback_running = False
                    release_opencv_camera()

            frame_placeholder = st.empty()

            if st.session_state.opencv_fallback_running:
                if st.session_state.opencv_cap is None:
                    cap, active_index = open_camera_capture(st.session_state.preferred_camera_index)
                    if cap is None:
                        st.session_state.opencv_fallback_running = False
                        st.error("Unable to open webcam. Try a different Preferred Camera Index in the sidebar.")
                        st.stop()

                    st.session_state.opencv_cap = cap
                    st.session_state.active_camera_index = active_index

                cap = st.session_state.opencv_cap
                active_index = st.session_state.active_camera_index
                ret, frame = cap.read()

                if not ret:
                    # Try reopening once before stopping the stream.
                    release_opencv_camera()
                    cap, active_index = open_camera_capture(st.session_state.preferred_camera_index)
                    if cap is not None:
                        st.session_state.opencv_cap = cap
                        st.session_state.active_camera_index = active_index
                        ret, frame = cap.read()

                if not ret:
                    st.session_state.opencv_fallback_running = False
                    release_opencv_camera()
                    st.error("Unable to read from webcam in OpenCV fallback mode.")
                else:
                    st.caption(f"Using camera device index: {active_index}")
                    frame = cv2.flip(frame, 1)
                    result_frame, rep_count, angle, left_angle, right_angle, status = \
                        st.session_state.pushup_counter.process_frame(frame)

                    st.session_state.last_frame_metrics = {
                        "rep_count": rep_count,
                        "angle": angle,
                        "left_angle": left_angle,
                        "right_angle": right_angle,
                        "status": status,
                    }

                    frame_placeholder.image(
                        cv2.cvtColor(result_frame, cv2.COLOR_BGR2RGB),
                        channels="RGB",
                        use_column_width=True,
                    )
                    time.sleep(0.02)
                    st.rerun()
            else:
                if st.session_state.opencv_cap is not None:
                    release_opencv_camera()
                st.caption("OpenCV fallback camera is idle. Click Start OpenCV Camera.")

        metrics = st.session_state.last_frame_metrics
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Total Reps", metrics["rep_count"])
        with col_b:
            st.metric("Elbow Angle", f"{metrics['angle']:.1f}°")
        with col_c:
            st.metric("Status", metrics["status"])

        st.info(
            f"👈 Left Elbow: {metrics['left_angle']:.1f}° | "
            f"Right Elbow: {metrics['right_angle']:.1f}°"
        )

        if camera_backend == "WebRTC (experimental)" and webrtc_ctx is not None and not webrtc_ctx.state.playing:
            st.caption("Camera is idle. Click START on the webcam panel to begin live counting.")
    
    else:  # Upload Video mode
        st.subheader("📤 Upload & Process Video")
        
        uploaded_file = st.file_uploader(
            "Upload a video file (MP4, AVI, MOV, MKV)",
            type=["mp4", "avi", "mov", "mkv"]
        )
        
        if uploaded_file is not None:
            # Save uploaded file temporarily
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            temp_file.write(uploaded_file.read())
            temp_file.close()
            
            # Open video
            cap = cv2.VideoCapture(temp_file.name)
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            st.info(f"📊 Video Info: {frame_count} frames @ {fps} FPS ({duration:.1f}s)")
            
            # Process button
            if st.button("🎬 Process Video", use_container_width=True):
                # Reset counter for new video
                st.session_state.pushup_counter.reset()
                
                progress_bar = st.progress(0)
                frame_placeholder = st.empty()
                stats_placeholder = st.empty()
                
                frame_idx = 0
                angles_log = []
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Resize for faster processing
                    frame = cv2.resize(frame, (640, 480))
                    
                    # Process frame
                    result_frame, rep_count, angle, left_angle, right_angle, status = \
                        st.session_state.pushup_counter.process_frame(frame)
                    
                    angles_log.append(angle)
                    
                    # Update display every 10 frames
                    if frame_idx % 10 == 0 or frame_idx == frame_count - 1:
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
                        - Progress: **{frame_idx}/{frame_count}**
                        """)
                    
                    # Update progress
                    progress = (frame_idx + 1) / frame_count
                    progress_bar.progress(min(progress, 0.99))
                    frame_idx += 1
                
                cap.release()
                os.unlink(temp_file.name)
                
                progress_bar.progress(1.0)
                st.success(f"✅ Video Processing Complete! Total Reps: **{rep_count}**")
                
                # Show angle graph
                st.subheader("📈 Angle Analysis")
                import matplotlib.pyplot as plt
                fig, ax = plt.subplots(figsize=(12, 4))
                ax.plot(angles_log, linewidth=2, label="Elbow Angle")
                ax.axhline(y=angle_down, color='r', linestyle='--', label=f'Down ({angle_down}°)')
                ax.axhline(y=angle_up, color='g', linestyle='--', label=f'Up ({angle_up}°)')
                ax.set_xlabel('Frame Number')
                ax.set_ylabel('Angle (degrees)')
                ax.set_title('Elbow Angle Over Time')
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)

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
- Move at a normal pace for accurate counting
- Maintain a consistent pushup form
- Get your elbows close to your body

**🔧 Troubleshooting:**
- If reps aren't being counted: Adjust angle thresholds in settings
- If person isn't detected: Check camera angle and lighting
- For accurate results: Test with different videos first

**📱 Mode Descriptions:**
- **Webcam Mode**: Continuous live webcam counting in real time
- **Video Mode**: Upload a complete video to analyze all reps at once
""")
