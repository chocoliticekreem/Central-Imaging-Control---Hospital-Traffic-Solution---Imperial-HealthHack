"""
Entity Definitions
==================
Simplified entities for location tracking system.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional
import time
import uuid


# ELR status levels (from NHS Electronic Locating Record)
ELRStatus = Literal["critical", "urgent", "standard", "stable"]


@dataclass
class TrackedPerson:
    """
    A person detected and tracked by the camera system.
    May or may not be linked to a patient record.
    """
    track_id: str                          # Internal tracking ID (from CV)
    position: tuple[int, int]              # (x, y) in camera pixels
    map_position: tuple[int, int] = (0, 0) # (x, y) on floor plan
    person_type: Literal["staff", "patient", "unknown"] = "unknown"
    last_seen: float = field(default_factory=time.time)

    # Link to patient record (set when nurse tags this person)
    patient_id: Optional[str] = None       # e.g., "P-4523" from ELR

    @property
    def is_tagged(self) -> bool:
        """Returns True if this tracked person is linked to a patient ID."""
        return self.patient_id is not None

    def time_since_seen(self) -> float:
        return time.time() - self.last_seen


@dataclass
class PatientRecord:
    """
    Patient information from ELR system.
    Linked to a TrackedPerson via patient_id.
    """
    patient_id: str                        # e.g., "P-4523"
    name: str                              # e.g., "John Smith"
    status: ELRStatus = "stable"           # From ELR feed
    chief_complaint: str = ""              # e.g., "Chest pain"
    wait_time_mins: int = 0                # Minutes since arrival

    @property
    def status_color(self) -> str:
        """Return color for map display."""
        return {
            "critical": "#dc3545",   # Red
            "urgent": "#fd7e14",     # Orange
            "standard": "#ffc107",   # Yellow
            "stable": "#28a745"      # Green
        }.get(self.status, "#6c757d")


@dataclass
class CameraZone:
    """
    Maps a camera to a region on the floor plan.
    """
    camera_id: str
    camera_name: str                       # e.g., "Corridor A"

    # Bounding box on floor plan where this camera's detections appear
    map_x: int                             # Top-left X on floor plan
    map_y: int                             # Top-left Y on floor plan
    map_width: int                         # Width of zone on floor plan
    map_height: int                        # Height of zone on floor plan

    # Camera frame dimensions (for scaling)
    camera_width: int = 1280
    camera_height: int = 720

    def camera_to_map(self, cam_x: int, cam_y: int) -> tuple[int, int]:
        """Convert camera pixel coordinates to floor plan coordinates."""
        # Scale camera position to map zone
        scale_x = self.map_width / self.camera_width
        scale_y = self.map_height / self.camera_height

        map_x = self.map_x + int(cam_x * scale_x)
        map_y = self.map_y + int(cam_y * scale_y)

        return (map_x, map_y)
