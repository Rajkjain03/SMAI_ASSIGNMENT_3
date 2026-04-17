import mediapipe as mp
import cv2
import numpy as np
from typing import Tuple, Dict, List

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils


class PoseDetector:
    """
    Detects human pose using MediaPipe.
    Provides methods to extract keypoints and calculate angles.
    """
    
    def __init__(self):
        """Initialize MediaPipe Pose detector."""
        self.pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def detect_pose(self, frame: np.ndarray) -> Tuple[np.ndarray, List[float]]:
        """
        Detect pose landmarks in a frame.
        
        Args:
            frame: Input video frame (BGR format from OpenCV)
            
        Returns:
            Annotated frame and list of landmark coordinates
        """
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame_rgb)
        
        # Draw pose landmarks
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                mp_drawing.DrawingSpec(color=(255, 0, 0), thickness=2)
            )
        
        landmarks = []
        if results.pose_landmarks:
            for landmark in results.pose_landmarks.landmark:
                landmarks.append([landmark.x, landmark.y, landmark.z, landmark.visibility])
        
        return frame, landmarks
    
    def get_landmark_position(self, landmarks: List[float], landmark_idx: int) -> Tuple[float, float]:
        """
        Get (x, y) position of a specific landmark.
        
        Args:
            landmarks: List of landmarks from detect_pose
            landmark_idx: Index of the landmark (0-32)
            
        Returns:
            (x, y) normalized coordinates
        """
        if landmark_idx < len(landmarks):
            return landmarks[landmark_idx][0], landmarks[landmark_idx][1]
        return None, None
    
    def calculate_angle(self, point1: Tuple[float, float], 
                       point2: Tuple[float, float], 
                       point3: Tuple[float, float]) -> float:
        """
        Calculate angle between three points using the law of cosines.
        
        Args:
            point1: (x1, y1) coordinates of first point
            point2: (x2, y2) coordinates of second point (vertex)
            point3: (x3, y3) coordinates of third point
            
        Returns:
            Angle in degrees
        """
        if None in point1 or None in point2 or None in point3:
            return 0
        
        x1, y1 = point1
        x2, y2 = point2
        x3, y3 = point3
        
        # Calculate vectors
        v1 = np.array([x1 - x2, y1 - y2])
        v2 = np.array([x3 - x2, y3 - y2])
        
        # Calculate angle using dot product
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
        
        return np.degrees(angle)
    
    def get_frame_dimensions(self, frame: np.ndarray) -> Tuple[int, int]:
        """Get frame height and width."""
        return frame.shape[0], frame.shape[1]


# MediaPipe landmark indices for reference
LANDMARKS = {
    'NOSE': 0,
    'LEFT_EYE': 1,
    'RIGHT_EYE': 2,
    'LEFT_EAR': 3,
    'RIGHT_EAR': 4,
    'LEFT_SHOULDER': 11,
    'RIGHT_SHOULDER': 12,
    'LEFT_ELBOW': 13,
    'RIGHT_ELBOW': 14,
    'LEFT_WRIST': 15,
    'RIGHT_WRIST': 16,
    'LEFT_HIP': 23,
    'RIGHT_HIP': 24,
    'LEFT_KNEE': 25,
    'RIGHT_KNEE': 26,
    'LEFT_ANKLE': 27,
    'RIGHT_ANKLE': 28,
}
