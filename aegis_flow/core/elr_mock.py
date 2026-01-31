"""
Mock ELR (Electronic Locating Record) Feed
==========================================
Simulates NHS ELR system with NEWS2 scores.
"""

import time
from typing import Dict, List, Optional
from .entities import PatientRecord


def create_demo_patients() -> List[PatientRecord]:
    """Create demo patients with realistic NEWS2 data."""
    now = time.time()

    patients = [
        # HIGH RISK (NEWS2 >= 7)
        PatientRecord(
            patient_id="P-1001",
            name="James Wilson",
            chief_complaint="Chest pain, SOB",
            arrival_time=now - 2700,  # 45 min ago
            respiratory_rate=28,       # High
            oxygen_saturation=89,      # Low
            systolic_bp=95,            # Low
            pulse=125,                 # High
            temperature=38.5,
            consciousness="Alert"
        ),
        PatientRecord(
            patient_id="P-1006",
            name="Lisa Anderson",
            chief_complaint="Stroke symptoms",
            arrival_time=now - 720,    # 12 min ago
            respiratory_rate=22,
            oxygen_saturation=92,
            systolic_bp=185,           # High
            pulse=88,
            temperature=37.2,
            consciousness="Voice"      # Reduced consciousness
        ),

        # MEDIUM RISK (NEWS2 5-6)
        PatientRecord(
            patient_id="P-1002",
            name="Sarah Connor",
            chief_complaint="Difficulty breathing",
            arrival_time=now - 1920,   # 32 min ago
            respiratory_rate=22,
            oxygen_saturation=93,
            systolic_bp=135,
            pulse=105,
            temperature=37.8,
            consciousness="Alert"
        ),
        PatientRecord(
            patient_id="P-1005",
            name="Robert Chen",
            chief_complaint="Head injury",
            arrival_time=now - 3120,   # 52 min ago
            respiratory_rate=18,
            oxygen_saturation=95,
            systolic_bp=145,
            pulse=92,
            temperature=37.0,
            consciousness="Alert"
        ),

        # LOW RISK (NEWS2 0-4)
        PatientRecord(
            patient_id="P-1003",
            name="Michael Brown",
            chief_complaint="Abdominal pain",
            arrival_time=now - 1680,   # 28 min ago
            respiratory_rate=16,
            oxygen_saturation=98,
            systolic_bp=125,
            pulse=78,
            temperature=37.1,
            consciousness="Alert"
        ),
        PatientRecord(
            patient_id="P-1004",
            name="Emma Thompson",
            chief_complaint="Minor laceration",
            arrival_time=now - 900,    # 15 min ago
            respiratory_rate=14,
            oxygen_saturation=99,
            systolic_bp=118,
            pulse=72,
            temperature=36.8,
            consciousness="Alert"
        ),
        PatientRecord(
            patient_id="P-1007",
            name="David Martinez",
            chief_complaint="Back pain",
            arrival_time=now - 4020,   # 67 min ago
            respiratory_rate=15,
            oxygen_saturation=97,
            systolic_bp=130,
            pulse=80,
            temperature=36.9,
            consciousness="Alert"
        ),
        PatientRecord(
            patient_id="P-1008",
            name="Jennifer Lee",
            chief_complaint="Sprained ankle",
            arrival_time=now - 1380,   # 23 min ago
            respiratory_rate=14,
            oxygen_saturation=99,
            systolic_bp=115,
            pulse=68,
            temperature=36.7,
            consciousness="Alert"
        ),
    ]

    # Calculate NEWS2 scores
    for p in patients:
        p.calculate_news2()

    return patients


class ELRMock:
    """
    Mock ELR system for demo purposes.
    """

    def __init__(self):
        self._patients: Dict[str, PatientRecord] = {}
        self._load_demo_data()

    def _load_demo_data(self):
        """Load demo patients."""
        for patient in create_demo_patients():
            self._patients[patient.patient_id] = patient

    def get_patient(self, patient_id: str) -> Optional[PatientRecord]:
        """Get a patient record by ID."""
        return self._patients.get(patient_id)

    def get_all_patients(self) -> List[PatientRecord]:
        """Get all patient records."""
        return list(self._patients.values())

    def get_patients_by_risk(self, risk_level: str) -> List[PatientRecord]:
        """Get patients filtered by risk level (low/medium/high)."""
        return [p for p in self._patients.values() if p.risk_level == risk_level]

    def get_high_risk_patients(self) -> List[PatientRecord]:
        """Get all high and medium risk patients."""
        return [p for p in self._patients.values() if p.risk_level in ("high", "medium")]

    def update_vitals(
        self,
        patient_id: str,
        respiratory_rate: int = None,
        oxygen_saturation: int = None,
        systolic_bp: int = None,
        pulse: int = None,
        temperature: float = None,
        consciousness: str = None
    ):
        """
        Update a patient's vital signs and recalculate NEWS2.
        Simulates receiving updated observations from clinical staff.
        """
        patient = self._patients.get(patient_id)
        if not patient:
            return

        if respiratory_rate is not None:
            patient.respiratory_rate = respiratory_rate
        if oxygen_saturation is not None:
            patient.oxygen_saturation = oxygen_saturation
        if systolic_bp is not None:
            patient.systolic_bp = systolic_bp
        if pulse is not None:
            patient.pulse = pulse
        if temperature is not None:
            patient.temperature = temperature
        if consciousness is not None:
            patient.consciousness = consciousness

        # Recalculate NEWS2
        patient.calculate_news2()

    def update_news2(self, patient_id: str, news2_score: int):
        """Directly set NEWS2 score (for demo purposes)."""
        if patient_id in self._patients:
            self._patients[patient_id].news2_score = news2_score

    def add_patient(self, patient: PatientRecord):
        """Add a new patient record."""
        patient.calculate_news2()
        self._patients[patient.patient_id] = patient

    def discharge_patient(self, patient_id: str):
        """Remove a patient (discharged)."""
        if patient_id in self._patients:
            del self._patients[patient_id]

    # Demo helpers
    def demo_deteriorate(self, patient_id: str):
        """Demo: Make a patient's condition worse."""
        patient = self._patients.get(patient_id)
        if patient:
            patient.respiratory_rate = min(35, patient.respiratory_rate + 5)
            patient.oxygen_saturation = max(85, patient.oxygen_saturation - 4)
            patient.pulse = min(140, patient.pulse + 15)
            patient.calculate_news2()

    def demo_improve(self, patient_id: str):
        """Demo: Make a patient's condition better."""
        patient = self._patients.get(patient_id)
        if patient:
            patient.respiratory_rate = max(12, patient.respiratory_rate - 3)
            patient.oxygen_saturation = min(99, patient.oxygen_saturation + 3)
            patient.pulse = max(60, patient.pulse - 10)
            patient.consciousness = "Alert"
            patient.calculate_news2()
