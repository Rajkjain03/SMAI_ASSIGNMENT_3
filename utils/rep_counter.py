import cv2
import numpy as np
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
        self.down_frames = 0
        self.up_frames = 0
        self.frames_since_last_rep = 999
        self.cycle_min_angle = None
        self.cycle_max_angle = None

        # Debounce and cycle validation to prevent random movement from being counted.
        self.required_down_frames = 3
        self.required_up_frames = 3
        self.min_rep_interval_frames = 8
        self.min_cycle_angle_delta = 35

    def _compute_arm_angle(self, landmarks, shoulder_idx: int, elbow_idx: int, wrist_idx: int,
                           visibility_threshold: float = 0.5):
        """Return elbow angle for one arm when all required landmarks are confidently visible."""
        if max(shoulder_idx, elbow_idx, wrist_idx) >= len(landmarks):
            return None

        shoulder = landmarks[shoulder_idx]
        elbow = landmarks[elbow_idx]
        wrist = landmarks[wrist_idx]

        if (
            shoulder[3] < visibility_threshold
            or elbow[3] < visibility_threshold
            or wrist[3] < visibility_threshold
        ):
            return None

        return self.pose_detector.calculate_angle(
            (shoulder[0], shoulder[1]),
            (elbow[0], elbow[1]),
            (wrist[0], wrist[1]),
        )
        
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
        
        # Compute angles only when arm landmarks are confidently detected.
        left_angle = self._compute_arm_angle(
            landmarks,
            LANDMARKS['LEFT_SHOULDER'],
            LANDMARKS['LEFT_ELBOW'],
            LANDMARKS['LEFT_WRIST'],
        )
        right_angle = self._compute_arm_angle(
            landmarks,
            LANDMARKS['RIGHT_SHOULDER'],
            LANDMARKS['RIGHT_ELBOW'],
            LANDMARKS['RIGHT_WRIST'],
        )

        valid_angles = [angle for angle in [left_angle, right_angle] if angle is not None]
        if not valid_angles:
            return annotated_frame, self.rep_count, 0, 0, 0, "Pose not clear"

        if left_angle is not None and right_angle is not None and abs(left_angle - right_angle) > 45:
            return annotated_frame, self.rep_count, 0, left_angle, right_angle, "Unstable pose"

        # Average angle from whichever arm(s) are currently visible.
        avg_angle = sum(valid_angles) / len(valid_angles)
        self.recent_angles.append(avg_angle)
        smoothed_angle = sum(self.recent_angles) / len(self.recent_angles)
        self.frames_since_last_rep += 1

        if smoothed_angle < self.angle_threshold_down:
            self.down_frames += 1
        else:
            self.down_frames = 0

        if smoothed_angle > self.angle_threshold_up:
            self.up_frames += 1
        else:
            self.up_frames = 0
        
        # Detect state change with temporal debounce and cycle validation.
        if not self.is_down and self.down_frames >= self.required_down_frames:
            self.is_down = True
            self.cycle_min_angle = smoothed_angle
            self.cycle_max_angle = smoothed_angle
            status = "Down"
        else:
            if self.is_down:
                self.cycle_min_angle = min(self.cycle_min_angle, smoothed_angle)
                self.cycle_max_angle = max(self.cycle_max_angle, smoothed_angle)

                cycle_delta = self.cycle_max_angle - self.cycle_min_angle
                if (
                    self.up_frames >= self.required_up_frames
                    and self.frames_since_last_rep >= self.min_rep_interval_frames
                    and cycle_delta >= self.min_cycle_angle_delta
                ):
                    self.is_down = False
                    self.rep_count += 1
                    self.frames_since_last_rep = 0
                    self.cycle_min_angle = None
                    self.cycle_max_angle = None
                    status = "Rep completed!"
                else:
                    status = "Down"
            else:
                status = "Up"
        
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
        left_display = left_angle if left_angle is not None else 0
        right_display = right_angle if right_angle is not None else 0
        cv2.putText(annotated_frame, f"Left: {left_display:.1f}° Right: {right_display:.1f}°",
                   (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 1)
        
        return annotated_frame, self.rep_count, smoothed_angle, left_angle, right_angle, status
    
    def reset(self):
        """Reset the rep counter."""
        self.rep_count = 0
        self.is_down = False
        self.recent_angles.clear()
        self.frame_buffer.clear()
        self.down_frames = 0
        self.up_frames = 0
        self.frames_since_last_rep = 999
        self.cycle_min_angle = None
        self.cycle_max_angle = None
    
    def get_stats(self) -> dict:
        """Get current statistics."""
        return {
            'rep_count': self.rep_count,
            'is_down': self.is_down,
            'current_angle': sum(self.recent_angles) / len(self.recent_angles) if self.recent_angles else 0,
            'down_frames': self.down_frames,
            'up_frames': self.up_frames,
        }
