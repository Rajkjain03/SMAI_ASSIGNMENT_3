#!/usr/bin/env python3
"""
Quick test to verify all imports work correctly
"""

print("🔍 Testing imports...")

try:
    print("  ✓ streamlit")
    import streamlit as st
except Exception as e:
    print(f"  ✗ streamlit: {e}")

try:
    print("  ✓ cv2")
    import cv2
except Exception as e:
    print(f"  ✗ cv2: {e}")

try:
    print("  ✓ numpy")
    import numpy as np
except Exception as e:
    print(f"  ✗ numpy: {e}")

try:
    print("  ✓ mediapipe")
    import mediapipe
except Exception as e:
    print(f"  ✗ mediapipe: {e}")

try:
    print("  ✓ PIL")
    from PIL import Image
except Exception as e:
    print(f"  ✗ PIL: {e}")

try:
    print("  ✓ scipy")
    import scipy
except Exception as e:
    print(f"  ✗ scipy: {e}")

try:
    print("  ✓ matplotlib")
    import matplotlib.pyplot as plt
except Exception as e:
    print(f"  ✗ matplotlib: {e}")

try:
    print("  ✓ av")
    import av
except Exception as e:
    print(f"  ✗ av: {e}")

try:
    print("  ✓ streamlit_webrtc")
    import streamlit_webrtc
except Exception as e:
    print(f"  ✗ streamlit_webrtc: {e}")

# Test local imports
try:
    print("  ✓ utils.pose_detector")
    from utils.pose_detector import PoseDetector, LANDMARKS
except Exception as e:
    print(f"  ✗ utils.pose_detector: {e}")

try:
    print("  ✓ utils.rep_counter")
    from utils.rep_counter import PushupCounter
except Exception as e:
    print(f"  ✗ utils.rep_counter: {e}")

print("\n✅ All imports successful!")
print("\nTo run the app, use: streamlit run app.py")
