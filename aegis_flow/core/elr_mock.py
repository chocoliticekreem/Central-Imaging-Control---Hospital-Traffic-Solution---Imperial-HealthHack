"""
Mock ELR (Electronic Locating Record) Feed
==========================================
Simulates NHS ELR system providing patient status updates.
In production, this would be replaced with actual NHS API integration.
"""

import json
import time
import random
from typing import Dict, List, Optional
from dataclasses import asdict

from .entities import PatientRecord, ELRStatus


# Sample patient data for demo
DEMO_PATIENTS = [
    PatientRecord("P-1001", "James Wilson", "critical", "Chest pain", 45),
    PatientRecord("P-1002", "Sarah Connor", "urgent", "Difficulty breathing", 32),
    PatientRecord("P-1003", "Michael Brown", "standard", "Abdominal pain", 28),
    PatientRecord("P-1004", "Emma Thompson", "stable", "Minor laceration", 15),
    PatientRecord("P-1005", "Robert Chen", "urgent", "Head injury", 52),
    PatientRecord("P-1006", "Lisa Anderson", "critical", "Stroke symptoms", 12),
    PatientRecord("P-1007", "David Martinez", "standard", "Back pain", 67),
    PatientRecord("P-1008", "Jennifer Lee", "stable", "Sprained ankle", 23),
]


class ELRMock:
    """
    Mock ELR system for demo purposes.
    Provides patient records and status updates.
    """

    def __init__(self):
        self._patients: Dict[str, PatientRecord] = {}
        self._load_demo_data()

    def _load_demo_data(self):
        """Load demo patients."""
        for patient in DEMO_PATIENTS:
            self._patients[patient.patient_id] = patient

    def get_patient(self, patient_id: str) -> Optional[PatientRecord]:
        """Get a patient record by ID."""
        return self._patients.get(patient_id)

    def get_all_patients(self) -> List[PatientRecord]:
        """Get all patient records."""
        return list(self._patients.values())

    def get_patients_by_status(self, status: ELRStatus) -> List[PatientRecord]:
        """Get patients filtered by status."""
        return [p for p in self._patients.values() if p.status == status]

    def get_critical_patients(self) -> List[PatientRecord]:
        """Get all critical and urgent patients."""
        return [p for p in self._patients.values() if p.status in ("critical", "urgent")]

    def update_status(self, patient_id: str, new_status: ELRStatus):
        """Update a patient's status (for demo controls)."""
        if patient_id in self._patients:
            self._patients[patient_id].status = new_status

    def add_patient(self, patient: PatientRecord):
        """Add a new patient record."""
        self._patients[patient.patient_id] = patient

    def remove_patient(self, patient_id: str):
        """Remove a patient (discharged)."""
        if patient_id in self._patients:
            del self._patients[patient_id]

    def to_json(self) -> str:
        """Export all patients as JSON (simulates API response)."""
        data = {
            "timestamp": time.time(),
            "patients": [asdict(p) for p in self._patients.values()]
        }
        return json.dumps(data, indent=2)

    def load_from_json(self, json_str: str):
        """Load patients from JSON (simulates API fetch)."""
        data = json.loads(json_str)
        self._patients.clear()
        for p in data.get("patients", []):
            record = PatientRecord(**p)
            self._patients[record.patient_id] = record

    # Demo helpers
    def demo_escalate_random(self):
        """Demo: Randomly escalate a patient's status."""
        stable = [p for p in self._patients.values() if p.status == "stable"]
        if stable:
            patient = random.choice(stable)
            patient.status = "urgent"
            return patient
        return None

    def demo_resolve_random(self):
        """Demo: Randomly resolve a critical patient."""
        critical = [p for p in self._patients.values() if p.status == "critical"]
        if critical:
            patient = random.choice(critical)
            patient.status = "stable"
            return patient
        return None
