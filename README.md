# 💪 Pushup Rep Counter - T6.3

A real-time pushup rep counter built with **MediaPipe** pose estimation and **Streamlit**, using elbow angle detection to automatically count repetitions.

## 🎯 Project Overview

This project solves the problem of accurately tracking pushup reps without manual counting. The app uses MediaPipe's pose detection to:
- Extract body keypoints in real-time
- Calculate elbow angles from both arms
- Detect state changes (down ↔ up) and count repetitions
- Provide real-time visual feedback via a Streamlit web interface

**Team Size:** 1-3 students (Tier 1)  
**Time Budget:** 4-6 hours per person  
**Compute:** Works on CPU (no GPU needed)

## ✨ Features

- **📹 Live Webcam Mode**: Real-time rep counting from webcam feed
- **📤 Video Upload Mode**: Process recorded videos and get rep count
- **⚙️ Adjustable Thresholds**: Fine-tune angle detection for different body types
- **📊 Live Metrics**: Display angle, rep count, and form status
- **🎨 Visual Feedback**: Skeleton overlay and angle annotations on video
- **📈 Statistics Dashboard**: Track session performance

## 🛠️ Technology Stack

- **Streamlit** - Web app framework
- **MediaPipe** - Pose detection (33 keypoints, real-time on CPU)
- **OpenCV** - Video processing
- **NumPy** - Numerical computations
- **Streamlit-WebRTC** - Webcam support (optional)

## 📋 Project Structure

```
pushup_counter/
├── app.py                    # Main Streamlit application
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── utils/
│   ├── __init__.py
│   ├── pose_detector.py      # MediaPipe wrapper for pose detection
│   └── rep_counter.py        # Core rep counting logic
└── data/
    └── (test videos stored here)
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Webcam (for live mode)
- Internet connection (for first-time model download)

### Installation

1. **Clone or download the repository:**
   ```bash
   cd /home/rajkjain/Downloads/SMAI_ASSIGNMENT_3
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

## 📖 Usage Guide

### Live Webcam Mode
1. Select "📹 Live Webcam" from the sidebar
2. Click "▶️ Start" to begin
3. Position yourself in frame with elbows visible
4. Do pushups - reps will count automatically
5. Click "⏹️ Stop" to finish

### Video Upload Mode
1. Select "📤 Upload Video" from the sidebar
2. Upload an MP4/AVI/MOV file
3. Click "🎬 Process Video"
4. View results with frame-by-frame annotations

### Adjusting Settings
In the sidebar, you can customize:
- **Down Position Angle** (default: 90°) - Threshold for "down" position
- **Up Position Angle** (default: 150°) - Threshold for "up" position
- **Reset Counter** - Start fresh with new session

## 🔍 How It Works

### Pose Detection
- MediaPipe detects 33 body landmarks (joints, keypoints)
- Extracts elbow positions from both arms
- Real-time detection at ~30 FPS on CPU

### Rep Counting Logic
```
State Machine:
1. Detect elbow angles (left & right)
2. Average the two angles for robustness
3. Track state: DOWN (bent) or UP (extended)
4. When: DOWN → UP, increment rep counter
5. Angle thresholds determine transitions
```

### Key Landmarks Used
- Left Shoulder (index 11)
- Left Elbow (index 13)
- Left Wrist (index 15)
- Right Shoulder (index 12)
- Right Elbow (index 14)
- Right Wrist (index 16)

## 📊 Evaluation Metrics

The app provides:
- **Rep Count**: Total pushups completed
- **Elbow Angle**: Current angle in degrees (left & right separately)
- **Form Status**: UP (arms extended) or DOWN (arms bent)
- **Per-Frame Accuracy**: Smoothed over 5 frames to reduce jitter

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| No reps being counted | Adjust angle thresholds - try Down: 85°, Up: 155° |
| Person not detected | Check lighting, ensure full body visible, reduce glare |
| Jerky or flickering counts | Increase smoothing window (edit rep_counter.py) |
| Webcam permission denied | Grant camera access in system settings |
| Video upload fails | Use MP4 format, max 500MB recommended |

## 🧪 Testing

### Test on YouTube Videos
Download pushup videos from YouTube and use the "Upload Video" mode to test accuracy.

**Sample videos to test:**
- Slow, controlled pushups (should count accurately)
- Fast pushups (may miss some if too fast)
- Different body angles (test robustness)

### Manual Testing
1. Do 10 known pushups and verify count
2. Try different speeds and form variations
3. Test with different lighting conditions

## 📝 Implementation Notes

### Design Decisions
1. **Elbow Angle Usage**: Simple, robust metric that doesn't depend on body size/build
2. **Dual Arm Average**: Reduces single-arm error; works for one-armed users
3. **Smoothing Window**: 5-frame averaging prevents false transitions
4. **Threshold-Based**: No training needed; works immediately

### Potential Improvements
1. Add form feedback (keep back straight, elbows close to body)
2. Distinguish pushup types (wide, narrow, diamond, etc.)
3. Add multi-user support
4. Export session data as CSV
5. Add voice feedback via text-to-speech

## 📄 Deliverables Checklist

- [x] Working Streamlit web app
- [x] README with setup & usage instructions
- [x] requirements.txt with all dependencies
- [x] GitHub-ready structure
- [x] Comments and docstrings in code
- [x] Handles edge cases (no person detected, etc.)

## 📚 References

- [MediaPipe Pose Documentation](https://developers.google.com/mediapipe/solutions/vision/pose_detector)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [OpenCV Documentation](https://docs.opencv.org/)

## 🤝 Team Credits

Built as part of SMAI Assignment 3: Build a Real ML App  
IIIT Hyderabad, Academic Year 2025-26

## 📜 License

MIT License - Feel free to use and modify for educational purposes.

---

**Happy Counting! 💪**
