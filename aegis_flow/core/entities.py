"""
Entity Definitions
==================
Defines the Patient and Staff dataclasses that represent tracked entities.
"""

from dataclasses import dataclass, field
from typing import Literal
import time
import uuid


@dataclass
class Patient:
    """Represents a tracked patient in the system."""
    id: str
    position: tuple[int, int]  # (x, y) in pixels
    last_seen: float = field(default_factory=time.time)
    last_interaction: float = field(default_factory=time.time)
    state: Literal["safe", "at_risk", "critical"] = "safe"
    is_ghost: bool = False  # True if entity disappeared but timeout not exceeded
    bbox: tuple[int, int, int, int] = (0, 0, 0, 0)  # (x1, y1, x2, y2)

    # Stretch goal fields (uncomment when implementing manual tagging)
    # acuity_score: int = 3
    # check_in_interval: int = 300
    # manual_tag: str = ""

    def time_since_interaction(self) -> float:
        """Returns seconds since last staff interaction."""
        return time.time() - self.last_interaction

    def time_since_seen(self) -> float:
        """Returns seconds since entity was last detected."""
        return time.time() - self.last_seen

    @classmethod
    def create(cls, position: tuple[int, int], bbox: tuple[int, int, int, int] = (0, 0, 0, 0)) -> "Patient":
        """Factory method to create a new patient with generated ID."""
        return cls(
            id=f"P{uuid.uuid4().hex[:6].upper()}",
            position=position,
            bbox=bbox
        )


@dataclass
class Staff:
    """Represents a tracked staff member."""
    id: str
    position: tuple[int, int]
    last_seen: float = field(default_factory=time.time)
    bbox: tuple[int, int, int, int] = (0, 0, 0, 0)

    def time_since_seen(self) -> float:
        """Returns seconds since entity was last detected."""
        return time.time() - self.last_seen

    @classmethod
    def create(cls, position: tuple[int, int], bbox: tuple[int, int, int, int] = (0, 0, 0, 0)) -> "Staff":
        """Factory method to create a new staff with generated ID."""
        return cls(
            id=f"S{uuid.uuid4().hex[:6].upper()}",
            position=position,
            bbox=bbox
        )


@dataclass
class Interaction:
    """Records an interaction event between staff and patient."""
    staff_id: str
    patient_id: str
    timestamp: float = field(default_factory=time.time)
    duration: float = 0.0  # seconds
