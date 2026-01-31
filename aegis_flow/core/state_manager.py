"""
State Manager
=============
Central hub for tracking people and linking them to patient records.
"""

import time
from typing import Dict, List, Optional, Tuple
from threading import Lock

from .entities import TrackedPerson, PatientRecord, CameraZone
from .elr_mock import ELRMock
from .floor_plan import FloorPlan


class StateManager:
    """
    Manages all tracked people and their links to patient records.
    Thread-safe singleton.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Tracked people from cameras
        self._tracked: Dict[str, TrackedPerson] = {}

        # Patient tagging: track_id -> patient_id
        self._tags: Dict[str, str] = {}

        # ELR system (patient records)
        self.elr = ELRMock()

        # Floor plan
        self.floor_plan = FloorPlan()

        # Thread safety
        self._lock = Lock()

        # Ghost timeout (seconds)
        self.ghost_timeout = 30

    @classmethod
    def reset_instance(cls):
        """Reset singleton (for testing)."""
        cls._instance = None

    # =========================================================================
    # TRACKING UPDATES (called by CV pipeline)
    # =========================================================================

    def update_tracked(
        self,
        track_id: str,
        camera_id: str,
        position: tuple[int, int],
        person_type: str = "unknown"
    ) -> TrackedPerson:
        """
        Update or create a tracked person from camera detection.
        Automatically converts to map coordinates if zone is configured.
        """
        with self._lock:
            # Convert to map coordinates
            map_pos = self.floor_plan.camera_to_map(camera_id, position[0], position[1])

            if track_id in self._tracked:
                # Update existing
                person = self._tracked[track_id]
                person.position = position
                person.map_position = map_pos
                person.person_type = person_type
                person.last_seen = time.time()
            else:
                # Create new
                person = TrackedPerson(
                    track_id=track_id,
                    position=position,
                    map_position=map_pos,
                    person_type=person_type
                )
                self._tracked[track_id] = person

            # Restore patient tag if exists
            if track_id in self._tags:
                person.patient_id = self._tags[track_id]

            return person

    def remove_tracked(self, track_id: str):
        """Remove a tracked person (lost tracking)."""
        with self._lock:
            if track_id in self._tracked:
                del self._tracked[track_id]

    def cleanup_stale(self):
        """Remove tracked people not seen recently."""
        with self._lock:
            now = time.time()
            stale = [
                tid for tid, person in self._tracked.items()
                if (now - person.last_seen) > self.ghost_timeout
            ]
            for tid in stale:
                del self._tracked[tid]

    # =========================================================================
    # PATIENT TAGGING (nurse links tracked person to patient record)
    # =========================================================================

    def tag_patient(self, track_id: str, patient_id: str) -> bool:
        """
        Link a tracked person to a patient record.
        Returns True if successful.
        """
        with self._lock:
            if track_id not in self._tracked:
                return False

            # Verify patient exists in ELR
            if not self.elr.get_patient(patient_id):
                return False

            # Create the link
            self._tags[track_id] = patient_id
            self._tracked[track_id].patient_id = patient_id
            return True

    def untag_patient(self, track_id: str):
        """Remove patient link from a tracked person."""
        with self._lock:
            if track_id in self._tags:
                del self._tags[track_id]
            if track_id in self._tracked:
                self._tracked[track_id].patient_id = None

    def get_tag(self, track_id: str) -> Optional[str]:
        """Get patient_id for a tracked person."""
        return self._tags.get(track_id)

    # =========================================================================
    # QUERIES
    # =========================================================================

    def get_all_tracked(self) -> List[TrackedPerson]:
        """Get all currently tracked people."""
        with self._lock:
            self.cleanup_stale()
            return list(self._tracked.values())

    def get_tracked_patients(self) -> List[Tuple[TrackedPerson, PatientRecord]]:
        """Get all tracked people who are tagged as patients, with their records."""
        with self._lock:
            result = []
            for person in self._tracked.values():
                if person.patient_id:
                    record = self.elr.get_patient(person.patient_id)
                    if record:
                        result.append((person, record))
            return result

    def get_critical_locations(self) -> List[Tuple[TrackedPerson, PatientRecord]]:
        """Get locations of critical/urgent patients."""
        with self._lock:
            result = []
            for person in self._tracked.values():
                if person.patient_id:
                    record = self.elr.get_patient(person.patient_id)
                    if record and record.status in ("critical", "urgent"):
                        result.append((person, record))
            return result

    def get_untagged(self) -> List[TrackedPerson]:
        """Get tracked people not yet tagged as patients."""
        with self._lock:
            return [p for p in self._tracked.values() if not p.is_tagged]

    def get_stats(self) -> dict:
        """Get summary statistics."""
        with self._lock:
            tracked = list(self._tracked.values())
            tagged = [p for p in tracked if p.is_tagged]

            critical_locs = self.get_critical_locations()

            return {
                "total_tracked": len(tracked),
                "tagged_patients": len(tagged),
                "untagged": len(tracked) - len(tagged),
                "staff_count": sum(1 for p in tracked if p.person_type == "staff"),
                "critical_located": len([x for x in critical_locs if x[1].status == "critical"]),
                "urgent_located": len([x for x in critical_locs if x[1].status == "urgent"]),
            }

    # =========================================================================
    # DEMO HELPERS
    # =========================================================================

    def demo_add_person(
        self,
        camera_id: str = "cam_corridor",
        position: tuple[int, int] = (640, 360),
        person_type: str = "patient"
    ) -> TrackedPerson:
        """Demo: Add a tracked person manually."""
        import uuid
        track_id = f"T-{uuid.uuid4().hex[:4].upper()}"
        return self.update_tracked(track_id, camera_id, position, person_type)

    def demo_clear_all(self):
        """Demo: Clear all tracked people."""
        with self._lock:
            self._tracked.clear()
            self._tags.clear()

    def demo_setup(self):
        """Demo: Set up sample data for presentation."""
        # Set up floor plan zones
        self.floor_plan.setup_demo_zones()
        self.floor_plan.create_demo_floor_plan()

        # Add some tracked people
        p1 = self.demo_add_person("cam_corridor", (200, 300), "patient")
        p2 = self.demo_add_person("cam_corridor", (400, 500), "patient")
        p3 = self.demo_add_person("cam_waiting", (600, 400), "patient")
        p4 = self.demo_add_person("cam_waiting", (300, 200), "staff")
        p5 = self.demo_add_person("cam_triage", (640, 300), "patient")

        # Tag some as patients from ELR
        self.tag_patient(p1.track_id, "P-1001")  # Critical
        self.tag_patient(p2.track_id, "P-1002")  # Urgent
        self.tag_patient(p3.track_id, "P-1004")  # Stable
        self.tag_patient(p5.track_id, "P-1006")  # Critical
