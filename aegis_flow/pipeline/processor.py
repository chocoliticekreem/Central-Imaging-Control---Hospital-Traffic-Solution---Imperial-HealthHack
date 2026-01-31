"""
CV Processor
============
Main computer vision processing loop. Runs in a separate process.

Pipeline per frame:
1. Capture frame from webcam
2. Detect people (YOLO)
3. Track people (assign persistent IDs)
4. Classify as staff/patient (uniform color)
5. Send updates to UI via bridge
"""

import time
from multiprocessing import Process, Queue
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .bridge import PipelineBridge, PipelineMessage, EntityUpdate

# These imports will work once vision modules are implemented
# from ..vision import PersonDetector, CentroidTracker, UniformClassifier

try:
    from aegis_flow import config
except ImportError:
    import config


class CVProcessor:
    """
    Main CV processing pipeline.
    Runs in a separate process, sends updates via Queue.
    """

    def __init__(self, queue: Queue, camera_id: str = "cam_corridor"):
        self.queue = queue
        self.bridge = PipelineBridge(queue)
        self.camera_id = camera_id
        self.process: Process = None
        self._running = False

    def start(self):
        """Start CV processing in a separate process."""
        self._running = True
        self.process = Process(target=self._run)
        self.process.start()

    def stop(self):
        """Stop CV processing."""
        self._running = False
        if self.process:
            self.process.join(timeout=2)
            if self.process.is_alive():
                self.process.terminate()

    def _run(self):
        """
        Main processing loop.

        TODO for implementer:
        1. Initialize cv2.VideoCapture
        2. Initialize PersonDetector, CentroidTracker, UniformClassifier
        3. Loop: capture → detect → track → classify → send
        """
        import cv2
        import numpy as np

        # Initialize camera
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

        # TODO: Initialize vision components when implemented
        # detector = PersonDetector()
        # tracker = CentroidTracker()
        # classifier = UniformClassifier()

        fps_time = time.time()
        frame_count = 0

        while self._running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            # TODO: Replace with actual detection when implemented
            # detections = detector.detect(frame)
            # tracks = tracker.update(detections)
            # entities = []
            # for track_id, tracked in tracks.items():
            #     person_type = classifier.classify(frame, tracked.bbox)
            #     entities.append(EntityUpdate(
            #         entity_id=track_id,
            #         camera_id=self.camera_id,
            #         entity_type=person_type,
            #         position=tracked.centroid,
            #         bbox=tracked.bbox
            #     ))

            # For now, send empty frame
            entities = []

            # Calculate FPS
            frame_count += 1
            if time.time() - fps_time >= 1.0:
                fps = frame_count / (time.time() - fps_time)
                frame_count = 0
                fps_time = time.time()
            else:
                fps = 0

            # Encode frame
            frame_bytes = PipelineBridge.encode_frame(frame)

            # Send message
            message = PipelineMessage(
                entities=entities,
                frame_jpeg=frame_bytes,
                fps=fps,
                camera_id=self.camera_id
            )
            self.bridge.send(message)

            time.sleep(0.033)  # ~30 FPS cap

        cap.release()


def run_processor(queue: Queue, camera_id: str = "cam_corridor"):
    """Entry point for subprocess."""
    processor = CVProcessor(queue, camera_id)
    processor._running = True
    processor._run()
