"""
Person Detector
===============
YOLOv8-based person detection.
"""

from typing import List, Tuple
from dataclasses import dataclass
import numpy as np

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("Warning: ultralytics not installed. Run: pip install ultralytics")


@dataclass
class Detection:
    """Single person detection result."""
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float

    @property
    def center(self) -> Tuple[int, int]:
        """Center point of bounding box."""
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
    """

    def __init__(self, model_name: str = "yolov8n.pt", confidence: float = 0.5):
        """
        Args:
            model_name: YOLO model to use (yolov8n.pt is fastest)
            confidence: Minimum confidence threshold
        """
        self.confidence = confidence
        self.model = None

        if YOLO_AVAILABLE:
            print(f"Loading YOLO model: {model_name}")
            self.model = YOLO(model_name)
            print("YOLO model loaded!")
        else:
            print("YOLO not available - detector will return empty results")

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Detect all people in the frame.

        Args:
            frame: BGR image as numpy array

        Returns:
            List of Detection objects
        """
        if self.model is None:
            return []

        # Run inference
        results = self.model(frame, verbose=False)

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for i in range(len(boxes)):
                # Class 0 is 'person' in COCO
                cls = int(boxes.cls[i])
                conf = float(boxes.conf[i])

                if cls == 0 and conf >= self.confidence:
                    x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy()
                    detections.append(Detection(
                        bbox=(int(x1), int(y1), int(x2), int(y2)),
                        confidence=conf
                    ))

        return detections

    def detect_and_draw(self, frame: np.ndarray) -> Tuple[np.ndarray, List[Detection]]:
        """Detect and draw bounding boxes on frame."""
        import cv2

        detections = self.detect(frame)
        frame_copy = frame.copy()

        for det in detections:
            x1, y1, x2, y2 = det.bbox
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame_copy, f"{det.confidence:.2f}",
                       (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        return frame_copy, detections
