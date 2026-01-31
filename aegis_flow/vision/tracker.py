"""
Centroid Tracker
================
Assigns persistent IDs to detected people across frames.
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from collections import OrderedDict
import numpy as np
import time

from .detector import Detection


@dataclass
class TrackedPerson:
    """A person being tracked across frames."""
    track_id: str
    centroid: Tuple[int, int]
    bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)
    missed_frames: int = 0
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)

    def update(self, centroid: Tuple[int, int], bbox: Tuple[int, int, int, int]):
        """Update position, reset missed counter."""
        self.centroid = centroid
        self.bbox = bbox
        self.missed_frames = 0
        self.last_seen = time.time()


class CentroidTracker:
    """
    Simple centroid-based multi-object tracker.

    Matches detections to existing tracks based on Euclidean distance.
    """

    def __init__(self, max_distance: int = 80, max_missed: int = 15):
        """
        Args:
            max_distance: Max pixels to consider same person
            max_missed: Frames before removing lost track
        """
        self.max_distance = max_distance
        self.max_missed = max_missed
        self.next_id = 1
        self.tracks: OrderedDict[str, TrackedPerson] = OrderedDict()

    def update(self, detections: List[Detection]) -> Dict[str, TrackedPerson]:
        """
        Update tracks with new detections.

        Returns:
            Dict of track_id -> TrackedPerson
        """
        # If no detections, increment missed for all tracks
        if len(detections) == 0:
            for track_id in list(self.tracks.keys()):
                self.tracks[track_id].missed_frames += 1
                if self.tracks[track_id].missed_frames > self.max_missed:
                    del self.tracks[track_id]
            return dict(self.tracks)

        # Get detection centroids
        input_centroids = np.array([d.center for d in detections])
        input_bboxes = [d.bbox for d in detections]

        # If no existing tracks, register all detections
        if len(self.tracks) == 0:
            for i, centroid in enumerate(input_centroids):
                self._register(tuple(centroid), input_bboxes[i])
            return dict(self.tracks)

        # Get existing track centroids
        track_ids = list(self.tracks.keys())
        track_centroids = np.array([self.tracks[tid].centroid for tid in track_ids])

        # Compute distance matrix
        distances = self._compute_distances(track_centroids, input_centroids)

        # Greedy matching: match closest pairs first
        used_detections = set()
        used_tracks = set()

        # Sort by distance
        rows, cols = np.where(distances < self.max_distance)
        if len(rows) > 0:
            sorted_indices = np.argsort(distances[rows, cols])

            for idx in sorted_indices:
                row, col = rows[idx], cols[idx]

                if row in used_tracks or col in used_detections:
                    continue

                # Update existing track
                track_id = track_ids[row]
                self.tracks[track_id].update(
                    tuple(input_centroids[col]),
                    input_bboxes[col]
                )

                used_tracks.add(row)
                used_detections.add(col)

        # Register unmatched detections as new tracks
        for col in range(len(detections)):
            if col not in used_detections:
                self._register(tuple(input_centroids[col]), input_bboxes[col])

        # Increment missed for unmatched tracks
        for row in range(len(track_ids)):
            if row not in used_tracks:
                track_id = track_ids[row]
                self.tracks[track_id].missed_frames += 1

        # Remove stale tracks
        for track_id in list(self.tracks.keys()):
            if self.tracks[track_id].missed_frames > self.max_missed:
                del self.tracks[track_id]

        return dict(self.tracks)

    def _register(self, centroid: Tuple[int, int], bbox: Tuple[int, int, int, int]) -> str:
        """Create a new track."""
        track_id = f"T-{self.next_id:04d}"
        self.tracks[track_id] = TrackedPerson(
            track_id=track_id,
            centroid=centroid,
            bbox=bbox
        )
        self.next_id += 1
        return track_id

    def _compute_distances(self, tracks: np.ndarray, detections: np.ndarray) -> np.ndarray:
        """Compute Euclidean distance matrix."""
        # tracks: (N, 2), detections: (M, 2)
        # output: (N, M) distance matrix
        diff = tracks[:, np.newaxis, :] - detections[np.newaxis, :, :]
        return np.sqrt(np.sum(diff ** 2, axis=2))

    def get_track(self, track_id: str) -> Optional[TrackedPerson]:
        """Get a specific track by ID."""
        return self.tracks.get(track_id)

    def clear(self):
        """Clear all tracks."""
        self.tracks.clear()
        self.next_id = 1
