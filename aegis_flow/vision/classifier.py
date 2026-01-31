"""
Uniform Classifier
==================
Classifies detected people as staff or patient based on clothing color.
"""

from typing import Literal, Tuple
import numpy as np
import cv2


class UniformClassifier:
    """
    Classifies people as staff or patient based on clothing color.

    Staff: Green (surgical scrubs)
    Patient: White/gray or other colors
    """

    def __init__(self):
        # Green range for staff (HSV)
        self.staff_lower = np.array([35, 40, 40])
        self.staff_upper = np.array([85, 255, 255])

        # Blue range for staff alternative (HSV)
        self.staff_blue_lower = np.array([100, 40, 40])
        self.staff_blue_upper = np.array([130, 255, 255])

        # Minimum ratio of colored pixels to classify as staff
        self.staff_threshold = 0.15

    def classify(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Literal["staff", "patient"]:
        """
        Classify a detected person as staff or patient.

        Args:
            frame: Full BGR image
            bbox: (x1, y1, x2, y2) bounding box

        Returns:
            "staff" or "patient"
        """
        x1, y1, x2, y2 = bbox

        # Validate bbox
        if x1 >= x2 or y1 >= y2:
            return "patient"

        # Get upper body region (torso)
        h = y2 - y1
        torso_y1 = max(0, y1 + int(h * 0.15))
        torso_y2 = min(frame.shape[0], y1 + int(h * 0.55))
        x1 = max(0, x1)
        x2 = min(frame.shape[1], x2)

        torso = frame[torso_y1:torso_y2, x1:x2]

        if torso.size == 0:
            return "patient"

        # Convert to HSV
        hsv = cv2.cvtColor(torso, cv2.COLOR_BGR2HSV)

        # Check for green (staff scrubs)
        green_mask = cv2.inRange(hsv, self.staff_lower, self.staff_upper)
        green_ratio = cv2.countNonZero(green_mask) / green_mask.size

        # Check for blue (alternative staff color)
        blue_mask = cv2.inRange(hsv, self.staff_blue_lower, self.staff_blue_upper)
        blue_ratio = cv2.countNonZero(blue_mask) / blue_mask.size

        # If enough green or blue pixels, classify as staff
        if green_ratio > self.staff_threshold or blue_ratio > self.staff_threshold:
            return "staff"

        return "patient"

    def get_dominant_color(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Tuple[int, int, int]:
        """
        Get the dominant color in the torso region.

        Returns:
            (H, S, V) tuple of dominant color
        """
        x1, y1, x2, y2 = bbox
        h = y2 - y1

        torso_y1 = max(0, y1 + int(h * 0.15))
        torso_y2 = min(frame.shape[0], y1 + int(h * 0.55))

        torso = frame[torso_y1:torso_y2, x1:x2]

        if torso.size == 0:
            return (0, 0, 0)

        hsv = cv2.cvtColor(torso, cv2.COLOR_BGR2HSV)

        # Calculate mean color
        mean_h = int(np.mean(hsv[:, :, 0]))
        mean_s = int(np.mean(hsv[:, :, 1]))
        mean_v = int(np.mean(hsv[:, :, 2]))

        return (mean_h, mean_s, mean_v)
