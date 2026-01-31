"""
Pipeline Bridge
===============
OWNER: Shared (Everyone should understand this)
DEPENDENCIES: multiprocessing

Connects the heavy CV processing (runs in separate process) to the
lightweight UI (Streamlit). Uses multiprocessing.Queue for thread-safe
communication.

Why separate processes?
- CV/YOLO is CPU/GPU intensive
- Streamlit needs to stay responsive
- Queue decouples the two, preventing lag

Message flow:
  CV Process --> Queue --> UI Process --> StateManager --> Dashboard

TODO for implementer:
1. Define message types and data format
2. Implement send/receive with timeout handling
3. Consider adding frame buffer for smooth video display
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from multiprocessing import Queue
import base64
import time


@dataclass
class EntityUpdate:
    """Update for a single tracked entity."""
    entity_id: str
    entity_type: str  # "staff" or "patient"
    position: tuple[int, int]
    bbox: tuple[int, int, int, int]


@dataclass
class InteractionUpdate:
    """Notification of a detected interaction."""
    staff_id: str
    patient_id: str
    duration: float


@dataclass
class PipelineMessage:
    """
    Message sent from CV process to UI process.

    Contains all updates from a single frame processing cycle.
    """
    timestamp: float = field(default_factory=time.time)
    entities: List[EntityUpdate] = field(default_factory=list)
    interactions: List[InteractionUpdate] = field(default_factory=list)
    frame_jpeg: Optional[bytes] = None  # JPEG-encoded frame for display
    fps: float = 0.0  # Current processing FPS


class PipelineBridge:
    """
    Bridge for CV-to-UI communication.

    Usage (CV side):
        bridge = PipelineBridge()
        # In processing loop:
        bridge.send(message)

    Usage (UI side):
        bridge = PipelineBridge(existing_queue)
        message = bridge.receive()
        if message:
            update_state_manager(message)

    TODO for implementer:
    1. __init__: Create or accept Queue
    2. send(): Non-blocking put with overflow handling
    3. receive(): Non-blocking get with timeout
    4. encode_frame(): Convert numpy array to JPEG bytes
    5. decode_frame(): Convert JPEG bytes back to numpy array
    """

    def __init__(self, queue: Optional[Queue] = None, max_size: int = 10):
        """
        Args:
            queue: Existing queue to use, or None to create new
            max_size: Maximum messages in queue before dropping old ones
        """
        self.queue = queue if queue else Queue(maxsize=max_size)
        self.max_size = max_size

    def send(self, message: PipelineMessage):
        """
        Send a message to the UI process.

        TODO:
        - If queue is full, drop oldest message first
        - Put new message in queue
        - Handle any exceptions gracefully
        """
        # TODO: Implement
        pass

    def receive(self, timeout: float = 0.1) -> Optional[PipelineMessage]:
        """
        Receive a message from the CV process.

        Args:
            timeout: How long to wait (seconds)

        Returns:
            PipelineMessage if available, None if timeout

        TODO:
        - Try to get from queue with timeout
        - Return None if queue.Empty exception
        """
        # TODO: Implement
        pass

    @staticmethod
    def encode_frame(frame) -> bytes:
        """
        Encode a numpy BGR frame to JPEG bytes.

        TODO:
        - Use cv2.imencode('.jpg', frame)
        - Return the bytes
        """
        # TODO: Implement
        pass

    @staticmethod
    def decode_frame(jpeg_bytes: bytes):
        """
        Decode JPEG bytes back to numpy BGR frame.

        TODO:
        - Use cv2.imdecode()
        - Return numpy array
        """
        # TODO: Implement
        pass
