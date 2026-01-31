"""
Pipeline Bridge
===============
Connects CV processing to UI via multiprocessing Queue.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from multiprocessing import Queue
from queue import Empty, Full
import time
import cv2
import numpy as np


@dataclass
class EntityUpdate:
    """Update for a single tracked entity."""
    entity_id: str
    camera_id: str
    entity_type: str  # "staff" or "patient"
    position: tuple[int, int]  # camera pixels
    bbox: tuple[int, int, int, int] = (0, 0, 0, 0)


@dataclass
class PipelineMessage:
    """Message sent from CV process to UI process."""
    timestamp: float = field(default_factory=time.time)
    camera_id: str = ""
    entities: List[EntityUpdate] = field(default_factory=list)
    frame_jpeg: Optional[bytes] = None
    fps: float = 0.0


class PipelineBridge:
    """
    Bridge for CV-to-UI communication.
    """

    def __init__(self, queue: Optional[Queue] = None, max_size: int = 10):
        self.queue = queue if queue else Queue(maxsize=max_size)
        self.max_size = max_size

    def send(self, message: PipelineMessage):
        """Send a message to the UI process (non-blocking)."""
        try:
            # Drop oldest if full
            if self.queue.full():
                try:
                    self.queue.get_nowait()
                except Empty:
                    pass
            self.queue.put_nowait(message)
        except Full:
            pass  # Skip this frame

    def receive(self, timeout: float = 0.1) -> Optional[PipelineMessage]:
        """Receive a message from the CV process."""
        try:
            return self.queue.get(timeout=timeout)
        except Empty:
            return None

    def receive_latest(self) -> Optional[PipelineMessage]:
        """Receive the most recent message, discarding older ones."""
        message = None
        try:
            while True:
                message = self.queue.get_nowait()
        except Empty:
            pass
        return message

    @staticmethod
    def encode_frame(frame: np.ndarray) -> bytes:
        """Encode a numpy BGR frame to JPEG bytes."""
        if frame is None:
            return b''
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return buffer.tobytes()

    @staticmethod
    def decode_frame(jpeg_bytes: bytes) -> Optional[np.ndarray]:
        """Decode JPEG bytes back to numpy BGR frame."""
        if not jpeg_bytes:
            return None
        arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
