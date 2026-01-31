"""
CV Processor
============
OWNER: Vision Team (Person B, C)
DEPENDENCIES: All vision modules, bridge.py, config.py

Main computer vision processing loop. Runs in a separate process
to keep the UI responsive.

Pipeline per frame:
1. Capture frame from webcam
2. Detect people (YOLO)
3. Track people (assign persistent IDs)
4. Classify as staff/patient (uniform color)
5. Detect interactions (proximity)
6. Send updates to UI via bridge

TODO for implementer:
1. Set up webcam capture
2. Initialize all vision components
3. Implement main processing loop
4. Handle graceful shutdown
"""

import time
from multiprocessing import Process, Queue
import cv2
import numpy as np

from .bridge import PipelineBridge, PipelineMessage, EntityUpdate, InteractionUpdate
from ..vision import PersonDetector, CentroidTracker, UniformClassifier, InteractionDetector
import config


class CVProcessor:
    """
    Main CV processing pipeline.

    Runs in a separate process, sends updates via Queue.

    Usage:
        queue = Queue()
        processor = CVProcessor(queue)
        processor.start()  # Starts separate process

        # In UI process:
        message = queue.get()

        # When done:
        processor.stop()

    TODO for implementer:
    1. __init__: Store queue, set running flag
    2. start(): Spawn process running _run()
    3. stop(): Set flag to stop, join process
    4. _run(): Main loop - capture, detect, track, classify, send
    5. _process_frame(): Single frame processing logic
    """

    def __init__(self, queue: Queue):
        """
        Args:
            queue: Queue to send messages to UI
        """
        self.queue = queue
        self.bridge = PipelineBridge(queue)
        self.process: Process = None
        self._running = False

    def start(self):
        """
        Start the CV processing in a separate process.

        TODO:
        - Set _running = True
        - Create Process targeting _run
        - Start the process
        """
        # TODO: Implement
        pass

    def stop(self):
        """
        Stop the CV processing.

        TODO:
        - Set _running = False
        - Join the process with timeout
        - Terminate if still running
        """
        # TODO: Implement
        pass

    def _run(self):
        """
        Main processing loop (runs in separate process).

        TODO:
        1. Initialize components:
           - cv2.VideoCapture(config.CAMERA_INDEX)
           - PersonDetector()
           - CentroidTracker()
           - UniformClassifier()
           - InteractionDetector()

        2. Main loop while self._running:
           - Read frame from camera
           - If frame is None, continue
           - Process frame
           - Calculate FPS
           - Send message via bridge
           - Small sleep to control rate

        3. Cleanup:
           - Release camera
        """
        # TODO: Implement
        pass

    def _process_frame(
        self,
        frame: np.ndarray,
        detector: PersonDetector,
        tracker: CentroidTracker,
        classifier: UniformClassifier,
        interaction_detector: InteractionDetector
    ) -> PipelineMessage:
        """
        Process a single frame through the full pipeline.

        Args:
            frame: BGR image from webcam
            detector: Person detector instance
            tracker: Centroid tracker instance
            classifier: Uniform classifier instance
            interaction_detector: Interaction detector instance

        Returns:
            PipelineMessage with all updates

        TODO:
        1. Detect people: detections = detector.detect(frame)
        2. Track people: tracks = tracker.update(detections)
        3. Classify each tracked person:
           - For each track, get bbox
           - person_type = classifier.classify(frame, bbox)
           - Create EntityUpdate
        4. Separate staff and patient tracks
        5. Detect interactions: interactions = interaction_detector.update(staff, patients)
        6. Encode frame to JPEG
        7. Build and return PipelineMessage
        """
        # TODO: Implement
        message = PipelineMessage()
        return message


def run_processor(queue: Queue):
    """
    Entry point for processor subprocess.

    This function is called when starting the CV process.
    Useful for multiprocessing.Process(target=run_processor, args=(queue,))
    """
    processor = CVProcessor(queue)
    processor._running = True
    processor._run()
