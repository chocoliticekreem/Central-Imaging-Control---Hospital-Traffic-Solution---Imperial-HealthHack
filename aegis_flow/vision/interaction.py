"""
Interaction Detector
====================
OWNER: Vision Team (Person D)
DEPENDENCIES: tracker.py, config.py

Detects when a staff member is interacting with a patient.
An "interaction" is defined as:
- Staff within INTERACTION_DISTANCE pixels of patient
- For at least INTERACTION_DURATION seconds

TODO for implementer:
1. Calculate distances between all staff-patient pairs
2. Track ongoing proximity (who has been close to whom, for how long)
3. Emit interaction event when duration threshold is met
4. Handle staff moving between patients
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import time
import math

from .tracker import TrackedPerson
import config


@dataclass
class ProximityEvent:
    """Tracks ongoing proximity between staff and patient."""
    staff_id: str
    patient_id: str
    start_time: float
    last_seen: float


@dataclass
class InteractionEvent:
    """Confirmed interaction (proximity exceeded duration threshold)."""
    staff_id: str
    patient_id: str
    duration: float


class InteractionDetector:
    """
    Detects staff-patient interactions based on proximity and duration.

    Usage:
        detector = InteractionDetector()
        interactions = detector.update(staff_tracks, patient_tracks)
        for interaction in interactions:
            state_manager.record_interaction(interaction.staff_id, interaction.patient_id)

    TODO for implementer:
    1. __init__: Initialize proximity tracking dict
    2. update(): Main detection logic
       - Calculate all pairwise distances
       - Update ongoing proximity events
       - Emit interactions when duration exceeded
       - Clean up ended proximities
    """

    def __init__(self):
        """Initialize proximity tracking."""
        # Maps (staff_id, patient_id) -> ProximityEvent
        self.active_proximities: Dict[Tuple[str, str], ProximityEvent] = {}

    def update(
        self,
        staff_tracks: Dict[str, TrackedPerson],
        patient_tracks: Dict[str, TrackedPerson]
    ) -> List[InteractionEvent]:
        """
        Check for new interactions based on current positions.

        Args:
            staff_tracks: Dict of staff_id -> TrackedPerson
            patient_tracks: Dict of patient_id -> TrackedPerson

        Returns:
            List of InteractionEvents for interactions that just completed

        TODO:
        1. For each staff-patient pair:
           - Calculate Euclidean distance between centroids
           - If distance < INTERACTION_DISTANCE:
             - If not in active_proximities: start new ProximityEvent
             - If in active_proximities: update last_seen
             - If duration > INTERACTION_DURATION: emit InteractionEvent
           - If distance >= INTERACTION_DISTANCE:
             - If was in active_proximities: remove it

        2. Clean up stale proximities (staff/patient no longer tracked)

        3. Return list of completed interactions
        """
        # TODO: Implement
        return []

    def _distance(self, p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
        """
        Calculate Euclidean distance between two points.

        TODO:
        - Use Pythagorean theorem: sqrt((x2-x1)^2 + (y2-y1)^2)
        """
        # TODO: Implement
        pass

    def _cleanup_stale(self, staff_ids: set, patient_ids: set):
        """
        Remove proximities where staff or patient is no longer tracked.

        TODO:
        - Iterate through active_proximities
        - Remove any where staff_id not in staff_ids
        - Remove any where patient_id not in patient_ids
        """
        # TODO: Implement
        pass
