from typing import Tuple, List
from collections import deque
from .pose_detector import PoseDetector, LANDMARKS


class PushupCounter:
    """
    Counts pushup repetitions based on elbow angle using MediaPipe pose detection.
    Uses a state machine to track pushup phases.
    """
    
    def __init__(self, angle_threshold_down: float = 90, angle_threshold_up: float = 150):
        """
        Initialize the pushup counter.
        
        Args:
            angle_threshold_down: Elbow angle threshold for "down" position (degrees)
            angle_threshold_up: Elbow angle threshold for "up" position (degrees)
        """
        self.pose_detector = PoseDetector()
        self.angle_threshold_down = angle_threshold_down
        self.angle_threshold_up = angle_threshold_up
        
        # State tracking
        self.rep_count = 0
        self.is_down = False  # True when in down position
        self.recent_angles = deque(maxlen=5)  # Smooth angle values
        self.frame_buffer = deque(maxlen=10)  # For debugging
        
    def process_frame(self, frame):
        """
        Process a single frame and update rep count if needed.
        
        Args:
            frame: Input video frame (BGR format)
            
        Returns:
            Tuple of (annotated_frame, rep_count, current_angle, left_angle, right_angle, status)
        """
        # Detect pose
        annotated_frame, landmarks = self.pose_detector.detect_pose(frame)
        
        if not landmarks:
            return annotated_frame, self.rep_count, 0, 0, 0, "No person detected"
        
        # Get elbow positions
        left_shoulder = self.pose_detector.get_landmark_position(
            landmarks, LANDMARKS['LEFT_SHOULDER']
        )
        left_elbow = self.pose_detector.get_landmark_position(
            landmarks, LANDMARKS['LEFT_ELBOW']
        )
        left_wrist = self.pose_detector.get_landmark_position(
            landmarks, LANDMARKS['LEFT_WRIST']
        )
        
        right_shoulder = self.pose_detector.get_landmark_position(
            landmarks, LANDMARKS['RIGHT_SHOULDER']
        )
        right_elbow = self.pose_detector.get_landmark_position(
            landmarks, LANDMARKS['RIGHT_ELBOW']
        )
        right_wrist = self.pose_detector.get_landmark_position(
            landmarks, LANDMARKS['RIGHT_WRIST']
        )
        
        # Calculate elbow angles
        left_angle = self.pose_detector.calculate_angle(
            left_shoulder, left_elbow, left_wrist
        )
        right_angle = self.pose_detector.calculate_angle(
            right_shoulder, right_elbow, right_wrist
        )
        
        # Average angle from both arms
        avg_angle = (left_angle + right_angle) / 2
        self.recent_angles.append(avg_angle)
        smoothed_angle = sum(self.recent_angles) / len(self.recent_angles)
        
        # Detect state change (down -> up = one rep)
        if not self.is_down and smoothed_angle < self.angle_threshold_down:
            # Entering down position
            self.is_down = True
            status = "Down"
        elif self.is_down and smoothed_angle > self.angle_threshold_up:
            # Exiting down position -> completing a rep
            self.is_down = False
            self.rep_count += 1
            status = "Rep completed!"
        else:
            status = "Down" if self.is_down else "Up"
        
        # Draw information on frame
        height, width = self.pose_detector.get_frame_dimensions(annotated_frame)
        
        # Draw angle on frame
        cv2.putText(annotated_frame, f"Angle: {smoothed_angle:.1f}°",
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Draw rep count
        cv2.putText(annotated_frame, f"Reps: {self.rep_count}",
                   (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 3)
        
        # Draw status
        status_color = (0, 255, 0) if status == "Up" else (0, 0, 255)
        cv2.putText(annotated_frame, f"Status: {status}",
                   (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
        
        # Draw individual angles for debugging
        cv2.putText(annotated_frame, f"Left: {left_angle:.1f}° Right: {right_angle:.1f}°",
                   (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        
        return annotated_frame, self.rep_count, smoothed_angle, left_angle, right_angle, status
    
    def reset(self):
        """Reset the rep counter."""
        self.rep_count = 0
        self.is_down = False
        self.recent_angles.clear()
        self.frame_buffer.clear()
    
    def get_stats(self) -> dict:
        """Get current statistics."""
        return {
            'rep_count': self.rep_count,
            'is_down': self.is_down,
            'current_angle': sum(self.recent_angles) / len(self.recent_angles) if self.recent_angles else 0
        }


# Import cv2 here for drawing functions
import cv2
