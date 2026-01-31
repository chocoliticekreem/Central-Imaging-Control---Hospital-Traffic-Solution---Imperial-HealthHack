"""
Centroid Tracker
================
OWNER: Vision Team (Person B, C)
DEPENDENCIES: detector.py, config.py

Assigns persistent IDs to detected people across frames.
Uses simple centroid tracking (Euclidean distance matching).

Key challenge: Handle flickering (person briefly undetected) without
losing track or creating duplicate IDs.

TODO for implementer:
1. Match new detections to existing tracks using distance
2. Handle new people entering frame (assign new ID)
3. Handle people leaving (mark as missing, don't delete immediately)
4. Implement FLICKER_THRESHOLD logic
"""

from typing import Dict, List, Tuple
from collections import OrderedDict
import numpy as np

from .detector import Detection
import config


class TrackedPerson:
    """A person being tracked across frames."""
    def __init__(self, person_id: str, centroid: Tuple[int, int]):
        self.id = person_id
        self.centroid = centroid
        self.missed_frames = 0  # consecutive frames not detected
        self.bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)

    def update(self, centroid: Tuple[int, int], bbox: Tuple[int, int, int, int]):
        """Update position, reset missed counter."""
        self.centroid = centroid
        self.bbox = bbox
        self.missed_frames = 0


class CentroidTracker:
    """
    Simple centroid-based multi-object tracker.

    Algorithm:
    1. For each new detection, find closest existing track
    2. If distance < threshold, update that track
    3. If no close track, create new one
    4. Increment missed_frames for unmatched tracks
    5. Remove tracks exceeding FLICKER_THRESHOLD missed frames

    TODO for implementer:
    1. __init__: Initialize ID counter and tracks dict
    2. update(): Main tracking logic
       - Calculate distances between detections and existing tracks
       - Use Hungarian algorithm or greedy matching
       - Handle new/lost tracks
    3. Consider using scipy.spatial.distance for efficiency
    """

    def __init__(self, max_distance: int = 50):
        """
        Args:
            max_distance: Maximum pixels to consider same person
        """
        self.next_id = 0
        self.tracks: OrderedDict[str, TrackedPerson] = OrderedDict()
        self.max_distance = max_distance

    def update(self, detections: List[Detection]) -> Dict[str, TrackedPerson]:
        """
        Update tracks with new detections.

        Args:
            detections: List of Detection objects from detector

        Returns:
            Dict mapping person_id -> TrackedPerson for all active tracks

        TODO:
        1. If no detections:
           - Increment missed_frames for all tracks
           - Remove tracks exceeding FLICKER_THRESHOLD
           - Return remaining tracks

        2. If no existing tracks:
           - Create new track for each detection
           - Return new tracks

        3. Otherwise:
           - Calculate distance matrix between detection centroids and track centroids
           - Match detections to tracks (greedy or Hungarian)
           - Update matched tracks
           - Create new tracks for unmatched detections
           - Increment missed_frames for unmatched tracks
           - Remove tracks exceeding threshold
        """
        # TODO: Implement
        return self.tracks

    def _register(self, centroid: Tuple[int, int], bbox: Tuple[int, int, int, int]) -> str:
        """
        Create a new track.

        TODO:
        - Create TrackedPerson with new ID
        - Increment self.next_id
        - Add to self.tracks
        - Return the new ID
        """
        # TODO: Implement
        pass

    def _deregister(self, person_id: str):
        """Remove a track by ID."""
        if person_id in self.tracks:
            del self.tracks[person_id]
