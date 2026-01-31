"""
Uniform Classifier
==================
OWNER: Vision Team (Person D)
DEPENDENCIES: config.py

Classifies detected people as "staff" or "patient" based on clothing color.
Uses HSV color space for robust color detection.

Staff: Green (surgical scrubs)
Patient: White/gray (hospital gowns)

TODO for implementer:
1. Extract upper body region from bounding box
2. Convert to HSV color space
3. Calculate dominant color or color histogram
4. Compare against configured color ranges
5. Return classification
"""

from typing import Literal, Tuple
import numpy as np
import cv2

import config


class UniformClassifier:
    """
    Classifies people as staff or patient based on clothing color.

    Usage:
        classifier = UniformClassifier()
        person_type = classifier.classify(frame, bbox)
        # Returns "staff" or "patient"

    TODO for implementer:
    1. __init__: Set up HSV ranges from config
    2. classify(): Main classification logic
    3. _extract_upper_body(): Get torso region from bbox
    4. _get_dominant_color(): Analyze color in region
    5. _match_color(): Check if color matches staff/patient range
    """

    def __init__(self):
        """
        Initialize color ranges from config.

        TODO:
        - Convert config.STAFF_COLOR to numpy arrays for cv2.inRange
        - Convert config.PATIENT_COLOR to numpy arrays for cv2.inRange
        """
        # TODO: Set up HSV ranges
        pass

    def classify(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Literal["staff", "patient"]:
        """
        Classify a detected person as staff or patient.

        Args:
            frame: Full BGR image
            bbox: (x1, y1, x2, y2) bounding box of detected person

        Returns:
            "staff" or "patient"

        TODO:
        1. Extract upper body region using _extract_upper_body
        2. Convert region to HSV
        3. Check if dominant color matches STAFF_COLOR range
        4. If yes, return "staff"
        5. Otherwise return "patient" (default)
        """
        # TODO: Implement
        return "patient"  # Default fallback

    def _extract_upper_body(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
        """
        Extract the upper body (torso) region from a bounding box.

        The upper body is typically the top 30-60% of the bounding box.
        This is where clothing color is most visible.

        TODO:
        - Calculate upper body region (top 30% to 60% of height)
        - Crop frame to that region
        - Return cropped region
        """
        # TODO: Implement
        pass

    def _get_dominant_color(self, region: np.ndarray) -> Tuple[int, int, int]:
        """
        Get the dominant HSV color in a region.

        Options:
        1. Simple: Average color (fast but affected by outliers)
        2. Better: Histogram peak (more robust)
        3. Best: K-means clustering (slow but accurate)

        TODO:
        - Convert region to HSV
        - Calculate dominant color using preferred method
        - Return (H, S, V) tuple
        """
        # TODO: Implement
        pass

    def _is_in_range(self, color: Tuple[int, int, int], color_range: dict) -> bool:
        """
        Check if a color falls within a specified HSV range.

        TODO:
        - Check H, S, V each within their respective ranges
        - Return True if all match, False otherwise
        """
        # TODO: Implement
        pass
