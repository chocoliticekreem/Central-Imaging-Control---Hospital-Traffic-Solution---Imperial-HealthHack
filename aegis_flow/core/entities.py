"""
Entity Definitions
==================
Entities for Re-ID based patient tracking with NEWS2 scoring.
"""

from dataclasses import dataclass, field
from typing import Literal, Optional, List
import time
import numpy as np


@dataclass
class PatientRecord:
    """
    Patient information from ELR system with NEWS2 score.
    """
    patient_id: str                        # e.g., "P-1234"
    name: str
    news2_score: int = 0                   # 0-20, calculated from vitals
    chief_complaint: str = ""
    arrival_time: float = field(default_factory=time.time)

    # Individual vital signs (for detailed view)
    respiratory_rate: int = 16             # breaths/min
    oxygen_saturation: int = 96            # %
    systolic_bp: int = 120                 # mmHg
    pulse: int = 75                        # bpm
    temperature: float = 37.0              # °C
    consciousness: str = "Alert"           # Alert, Voice, Pain, Unresponsive

    # Re-ID signature (stored when patient is enrolled)
    reid_signature: Optional[np.ndarray] = None

    @property
    def risk_level(self) -> Literal["low", "medium", "high"]:
        """Determine risk level from NEWS2 score."""
        if self.news2_score >= 7:
            return "high"
        elif self.news2_score >= 5:
            return "medium"
        return "low"

    @property
    def status_color(self) -> str:
        """Return color for map display based on NEWS2."""
        return {
            "high": "#dc3545",      # Red
            "medium": "#ffc107",    # Yellow
            "low": "#28a745"        # Green
        }[self.risk_level]

    @property
    def wait_time_mins(self) -> int:
        """Minutes since arrival."""
        return int((time.time() - self.arrival_time) / 60)

    def calculate_news2(self) -> int:
        """
        Calculate NEWS2 score from vital signs.
        Simplified version - real NEWS2 has more complex scoring.
        """
        score = 0

        # Respiratory rate scoring
        if self.respiratory_rate <= 8 or self.respiratory_rate >= 25:
            score += 3
        elif self.respiratory_rate >= 21:
            score += 2
        elif self.respiratory_rate <= 11:
            score += 1

        # Oxygen saturation scoring
        if self.oxygen_saturation <= 91:
            score += 3
        elif self.oxygen_saturation <= 93:
            score += 2
        elif self.oxygen_saturation <= 95:
            score += 1

        # Systolic BP scoring
        if self.systolic_bp <= 90 or self.systolic_bp >= 220:
            score += 3
        elif self.systolic_bp <= 100:
            score += 2
        elif self.systolic_bp <= 110:
            score += 1

        # Pulse scoring
        if self.pulse <= 40 or self.pulse >= 131:
            score += 3
        elif self.pulse >= 111:
            score += 2
        elif self.pulse <= 50 or self.pulse >= 91:
            score += 1

        # Temperature scoring
        if self.temperature <= 35.0:
            score += 3
        elif self.temperature >= 39.1:
            score += 2
        elif self.temperature <= 36.0 or self.temperature >= 38.1:
            score += 1

        # Consciousness scoring
        if self.consciousness != "Alert":
            score += 3

        self.news2_score = score
        return score


@dataclass
class TrackedPerson:
    """
    A person currently being tracked by the camera system.
    May be matched to a PatientRecord via Re-ID.
    """
    track_id: str                          # Internal tracking ID from CV
    position: tuple[int, int]              # (x, y) in camera pixels
    map_position: tuple[int, int] = (0, 0) # (x, y) on floor plan
    bbox: tuple[int, int, int, int] = (0, 0, 0, 0)
    person_type: Literal["staff", "patient", "unknown"] = "unknown"
    last_seen: float = field(default_factory=time.time)

    # Re-ID matching
    patient_id: Optional[str] = None       # Linked patient (via Re-ID match)
    reid_signature: Optional[np.ndarray] = None  # Visual signature for matching
    reid_confidence: float = 0.0           # Match confidence (0-1)

    @property
    def is_identified(self) -> bool:
        """Returns True if matched to a patient record."""
        return self.patient_id is not None

    def time_since_seen(self) -> float:
        return time.time() - self.last_seen


@dataclass
class CameraZone:
    """
    Maps a camera to a region on the floor plan.
    """
    camera_id: str
    camera_name: str                       # e.g., "Corridor A"

    # Bounding box on floor plan
    map_x: int
    map_y: int
    map_width: int
    map_height: int

    # Camera frame dimensions
    camera_width: int = 1280
    camera_height: int = 720

    def camera_to_map(self, cam_x: int, cam_y: int) -> tuple[int, int]:
        """Convert camera pixel coordinates to floor plan coordinates."""
        scale_x = self.map_width / self.camera_width
        scale_y = self.map_height / self.camera_height

        map_x = self.map_x + int(cam_x * scale_x)
        map_y = self.map_y + int(cam_y * scale_y)

        return (map_x, map_y)
