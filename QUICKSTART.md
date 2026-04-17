# Quick Start Guide - Pushup Rep Counter

## ⚡ 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the App
```bash
streamlit run app.py
```

### 3. Open Browser
```
http://localhost:8501
```

## 🎮 Using the App

### Live Mode
1. Select "📹 Live Webcam"
2. Allow camera access
3. Click "▶️ Start"
4. Do pushups - it will count automatically
5. Check real-time angle and rep count

### Video Mode
1. Select "📤 Upload Video"
2. Upload an MP4 file
3. Click "🎬 Process Video"
4. Wait for processing
5. View results with rep count

## ⚙️ Adjusting Settings

In the sidebar:
- **Down Angle**: How bent = "down" position
- **Up Angle**: How extended = "up" position
- **Reset**: Clear counter

**Default values work for most people!**

## 🔧 If It's Not Working

| Problem | Fix |
|---------|-----|
| No reps counting | Try: Down=80°, Up=160° |
| Not detecting person | Improve lighting, move closer |
| Counting extra reps | Try: Down=100°, Up=140° |
| Webcam not working | Check camera permissions |

## 📊 Understanding Metrics

- **Angle**: Bend at your elbow (lower = more bent)
- **Status**: UP (extended) or DOWN (bent)
- **Reps**: Total completed (DOWN→UP = +1)

## 💡 Tips

✓ Keep your full body in frame  
✓ Face the camera directly  
✓ Do reps at normal speed (not too fast)  
✓ Keep good lighting  
✗ Don't obstruct your elbows

---

**Questions?** Check README.md or troubleshooting section.
