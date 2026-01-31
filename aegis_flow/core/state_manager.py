"""
State Manager
=============
The CENTRAL HUB of the system. All entity state changes flow through here.
Both the CV pipeline and demo mode buttons update state via this manager.
"""

import time
from typing import Dict, List, Optional
from threading import Lock
import sys
import os

# Add parent to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from .entities import Patient, Staff, Interaction
from .scoring import calculate_priority

# Import config - handle both direct run and module import
try:
    from aegis_flow import config
except ImportError:
    try:
        import config
    except ImportError:
        # Fallback defaults if config not found
        class config:
            SAFE_THRESHOLD = 300
            AT_RISK_THRESHOLD = 900
            GHOST_TIMEOUT = 30


class StateManager:
    """
    Singleton state manager for all tracked entities.
    Thread-safe: Uses locks for concurrent access from CV and UI threads.
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

        self._patients: Dict[str, Patient] = {}
        self._staff: Dict[str, Staff] = {}
        self._interactions: List[Interaction] = []
        self._lock = Lock()

    @classmethod
    def reset_instance(cls):
        """Reset the singleton (useful for testing)."""
        cls._instance = None

    # =========================================================================
    # ENTITY UPDATES (called by CV pipeline or demo mode)
    # =========================================================================

    def update_patient(
        self,
        patient_id: str,
        position: tuple[int, int],
        bbox: tuple[int, int, int, int] = (0, 0, 0, 0)
    ) -> Patient:
        """Update or create a patient entity."""
        with self._lock:
            now = time.time()

            if patient_id in self._patients:
                # Update existing patient
                patient = self._patients[patient_id]
                patient.position = position
                patient.bbox = bbox
                patient.last_seen = now
                patient.is_ghost = False
            else:
                # Create new patient
                patient = Patient(
                    id=patient_id,
                    position=position,
                    bbox=bbox,
                    last_seen=now,
                    last_interaction=now  # New patients start with fresh timer
                )
                self._patients[patient_id] = patient

            self._update_patient_states()
            return patient

    def update_staff(
        self,
        staff_id: str,
        position: tuple[int, int],
        bbox: tuple[int, int, int, int] = (0, 0, 0, 0)
    ) -> Staff:
        """Update or create a staff entity."""
        with self._lock:
            now = time.time()

            if staff_id in self._staff:
                # Update existing staff
                staff = self._staff[staff_id]
                staff.position = position
                staff.bbox = bbox
                staff.last_seen = now
            else:
                # Create new staff
                staff = Staff(
                    id=staff_id,
                    position=position,
                    bbox=bbox,
                    last_seen=now
                )
                self._staff[staff_id] = staff

            return staff

    def mark_patient_missing(self, patient_id: str):
        """Mark a patient as missing (not detected in current frame)."""
        with self._lock:
            if patient_id in self._patients:
                self._patients[patient_id].is_ghost = True

    def mark_staff_missing(self, staff_id: str):
        """Mark a staff member as missing."""
        with self._lock:
            # Staff don't become ghosts, they just get cleaned up
            pass

    # =========================================================================
    # INTERACTION TRACKING
    # =========================================================================

    def record_interaction(self, staff_id: str, patient_id: str, duration: float = 0.0):
        """Record a staff-patient interaction."""
        with self._lock:
            # Create interaction record
            interaction = Interaction(
                staff_id=staff_id,
                patient_id=patient_id,
                duration=duration
            )
            self._interactions.append(interaction)

            # Update patient's last interaction time and state
            if patient_id in self._patients:
                self._patients[patient_id].last_interaction = time.time()
                self._patients[patient_id].state = "safe"

    # =========================================================================
    # STATE MANAGEMENT (internal, no lock needed - called within locked context)
    # =========================================================================

    def _update_patient_states(self):
        """Update all patient states based on time since last interaction."""
        now = time.time()

        for patient in self._patients.values():
            time_since = now - patient.last_interaction

            if time_since < config.SAFE_THRESHOLD:
                patient.state = "safe"
            elif time_since < config.AT_RISK_THRESHOLD:
                patient.state = "at_risk"
            else:
                patient.state = "critical"

    def _cleanup_ghosts(self):
        """Remove ghost entities that exceeded GHOST_TIMEOUT."""
        now = time.time()

        # Find patients to remove
        patients_to_remove = [
            pid for pid, patient in self._patients.items()
            if patient.is_ghost and (now - patient.last_seen) > config.GHOST_TIMEOUT
        ]
        for pid in patients_to_remove:
            del self._patients[pid]

        # Find staff to remove
        staff_to_remove = [
            sid for sid, staff in self._staff.items()
            if (now - staff.last_seen) > config.GHOST_TIMEOUT
        ]
        for sid in staff_to_remove:
            del self._staff[sid]

    # =========================================================================
    # QUERIES (called by dashboard)
    # =========================================================================

    def get_priority_list(self) -> List[Patient]:
        """Get all patients sorted by priority (highest first)."""
        with self._lock:
            self._update_patient_states()
            self._cleanup_ghosts()

            patients = list(self._patients.values())
            patients.sort(key=lambda p: calculate_priority(p), reverse=True)
            return patients

    def get_all_patients(self) -> Dict[str, Patient]:
        """Get all patients as a dict."""
        with self._lock:
            return dict(self._patients)

    def get_all_staff(self) -> List[Staff]:
        """Return all tracked staff."""
        with self._lock:
            return list(self._staff.values())

    def get_patient(self, patient_id: str) -> Optional[Patient]:
        """Get a specific patient by ID."""
        with self._lock:
            return self._patients.get(patient_id)

    def get_recent_interactions(self, limit: int = 10) -> List[Interaction]:
        """Get the most recent interactions."""
        with self._lock:
            return self._interactions[-limit:]

    def get_stats(self) -> dict:
        """Get summary statistics."""
        with self._lock:
            patients = list(self._patients.values())
            return {
                "total_patients": len(patients),
                "total_staff": len(self._staff),
                "safe_count": sum(1 for p in patients if p.state == "safe"),
                "at_risk_count": sum(1 for p in patients if p.state == "at_risk"),
                "critical_count": sum(1 for p in patients if p.state == "critical"),
                "total_interactions": len(self._interactions)
            }

    # =========================================================================
    # DEMO MODE HELPERS
    # =========================================================================

    def demo_add_patient(self, position: tuple[int, int] = (400, 300)) -> Patient:
        """Demo mode: Manually add a patient with generated ID."""
        patient = Patient.create(position=position)
        with self._lock:
            self._patients[patient.id] = patient
            return patient

    def demo_add_staff(self, position: tuple[int, int] = (200, 300)) -> Staff:
        """Demo mode: Manually add a staff member with generated ID."""
        staff = Staff.create(position=position)
        with self._lock:
            self._staff[staff.id] = staff
            return staff

    def demo_simulate_neglect(self, patient_id: str, minutes: float):
        """Demo mode: Fast-forward a patient's neglect time."""
        with self._lock:
            if patient_id in self._patients:
                # Subtract time to simulate neglect
                self._patients[patient_id].last_interaction -= (minutes * 60)
                self._update_patient_states()

    def demo_trigger_interaction(self, patient_id: str):
        """Demo mode: Simulate a staff interaction with patient."""
        self.record_interaction(
            staff_id="DEMO_STAFF",
            patient_id=patient_id,
            duration=5.0
        )

    def demo_clear_all(self):
        """Demo mode: Clear all entities for reset."""
        with self._lock:
            self._patients.clear()
            self._staff.clear()
            self._interactions.clear()

    def demo_set_patient_state(self, patient_id: str, state: str):
        """Demo mode: Directly set a patient's state."""
        with self._lock:
            if patient_id in self._patients:
                if state in ("safe", "at_risk", "critical"):
                    self._patients[patient_id].state = state
