"""
Person Detector
===============
OWNER: Vision Team (Person B, C)
DEPENDENCIES: ultralytics (YOLOv8), config.py

Wraps YOLOv8 for person detection. Returns bounding boxes for all
detected people in a frame.

TODO for implementer:
1. Initialize YOLOv8 model in __init__
2. Implement detect() to run inference and filter for person class
3. Consider adding batch processing for efficiency
"""

from typing import List, Tuple
import numpy as np

import config


class Detection:
    """Single person detection result."""
    def __init__(self, bbox: Tuple[int, int, int, int], confidence: float):
        self.bbox = bbox  # (x1, y1, x2, y2)
        self.confidence = confidence

    @property
    def center(self) -> Tuple[int, int]:
        """Calculate center point of bounding box."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    @property
    def width(self) -> int:
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> int:
        return self.bbox[3] - self.bbox[1]


class PersonDetector:
    """
    YOLOv8-based person detector.

    Usage:
        detector = PersonDetector()
        detections = detector.detect(frame)
        for det in detections:
            print(f"Person at {det.center} with confidence {det.confidence}")

    TODO for implementer:
    1. __init__: Load YOLO model using ultralytics
       - from ultralytics import YOLO
       - self.model = YOLO(config.YOLO_MODEL)

    2. detect(): Run inference on frame
       - results = self.model(frame)
       - Filter for class 0 (person) only
       - Filter by config.DETECTION_CONFIDENCE
       - Return list of Detection objects
    """

    def __init__(self):
        """
        Initialize the YOLO model.

        TODO:
        - Load YOLOv8 model: self.model = YOLO(config.YOLO_MODEL)
        - Handle case where model file doesn't exist (auto-downloads)
        """
        self.model = None  # TODO: Initialize YOLO model
        pass

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect all people in the frame.

        Args:
            frame: BGR image as numpy array (from OpenCV)

        Returns:
            List of Detection objects for each person found

        TODO:
        - Run self.model(frame)
        - Extract boxes, filter for person class (class_id == 0)
        - Filter by confidence threshold
        - Convert to Detection objects
        - Return list
        """
        # TODO: Implement
        return []
