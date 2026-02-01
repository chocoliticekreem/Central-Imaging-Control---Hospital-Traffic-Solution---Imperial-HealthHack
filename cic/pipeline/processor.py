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

# Vision components
from cic.vision.detector import PersonDetector
from cic.vision.tracker import CentroidTracker
from cic.vision.classifier import UniformClassifier

try:
    from cic import config
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
        """Main processing loop."""
        import cv2

        # Initialize camera
        cap = cv2.VideoCapture(config.CAMERA_INDEX)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

        # Initialize vision components
        print("Initializing vision components...")
        detector = PersonDetector(confidence=0.5)
        tracker = CentroidTracker(max_distance=80, max_missed=15)
        classifier = UniformClassifier()
        print("Vision components ready!")

        fps_time = time.time()
        frame_count = 0
        fps = 0

        while self._running:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            # 1. Detect people
            detections = detector.detect(frame)

            # 2. Track people (assign persistent IDs)
            tracks = tracker.update(detections)

            # 3. Classify and build entity updates
            entities = []
            for track_id, tracked in tracks.items():
                # Classify as staff/patient based on uniform color
                person_type = classifier.classify(frame, tracked.bbox)

                entities.append(EntityUpdate(
                    entity_id=track_id,
                    camera_id=self.camera_id,
                    entity_type=person_type,
                    position=tracked.centroid,
                    bbox=tracked.bbox
                ))

            # Calculate FPS
            frame_count += 1
            elapsed = time.time() - fps_time
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                frame_count = 0
                fps_time = time.time()

            # Encode frame for transmission
            frame_bytes = PipelineBridge.encode_frame(frame)

            # Send message to UI
            message = PipelineMessage(
                entities=entities,
                frame_jpeg=frame_bytes,
                fps=fps,
                camera_id=self.camera_id
            )
            self.bridge.send(message)

            # Cap at ~30 FPS
            time.sleep(0.033)

        cap.release()


def run_processor(queue: Queue, camera_id: str = "cam_corridor"):
    """Entry point for subprocess."""
    processor = CVProcessor(queue, camera_id)
    processor._running = True
    processor._run()


# Standalone test
if __name__ == "__main__":
    from multiprocessing import Queue
    import cv2

    print("Testing CV Processor standalone...")
    q = Queue()

    # Run in main thread for testing
    processor = CVProcessor(q, "cam_test")
    processor._running = True

    # Run for a few seconds
    import threading

    def run_for_seconds(seconds):
        time.sleep(seconds)
        processor._running = False

    t = threading.Thread(target=run_for_seconds, args=(10,))
    t.start()

    try:
        processor._run()
    except KeyboardInterrupt:
        processor._running = False

    print(f"Processed frames. Queue size: {q.qsize()}")
