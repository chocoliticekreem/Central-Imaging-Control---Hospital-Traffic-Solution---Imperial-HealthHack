// Mock data matching the Python backend structure

export const mockPatients = [
  {
    patient_id: "P-1001",
    name: "John Smith",
    age: 67,
    chief_complaint: "Chest pain, shortness of breath",
    news2_score: 9,
    risk_level: "high",
    status_color: "#dc3545",
    vitals: { hr: 112, bp_sys: 165, bp_dia: 95, rr: 24, temp: 38.2, spo2: 91 }
  },
  {
    patient_id: "P-1002",
    name: "Mary Johnson",
    age: 45,
    chief_complaint: "Severe abdominal pain",
    news2_score: 6,
    risk_level: "medium",
    status_color: "#ffc107",
    vitals: { hr: 98, bp_sys: 138, bp_dia: 88, rr: 20, temp: 37.8, spo2: 95 }
  },
  {
    patient_id: "P-1003",
    name: "Robert Williams",
    age: 72,
    chief_complaint: "Confusion, fever",
    news2_score: 7,
    risk_level: "high",
    status_color: "#dc3545",
    vitals: { hr: 105, bp_sys: 100, bp_dia: 60, rr: 22, temp: 38.9, spo2: 93 }
  },
  {
    patient_id: "P-1004",
    name: "Sarah Davis",
    age: 34,
    chief_complaint: "Minor laceration",
    news2_score: 1,
    risk_level: "low",
    status_color: "#28a745",
    vitals: { hr: 72, bp_sys: 118, bp_dia: 76, rr: 14, temp: 36.8, spo2: 99 }
  },
  {
    patient_id: "P-1005",
    name: "Michael Brown",
    age: 58,
    chief_complaint: "Diabetic emergency",
    news2_score: 5,
    risk_level: "medium",
    status_color: "#ffc107",
    vitals: { hr: 88, bp_sys: 145, bp_dia: 92, rr: 18, temp: 36.5, spo2: 96 }
  },
  {
    patient_id: "P-1006",
    name: "Emma Wilson",
    age: 81,
    chief_complaint: "Fall, hip pain",
    news2_score: 8,
    risk_level: "high",
    status_color: "#dc3545",
    vitals: { hr: 110, bp_sys: 95, bp_dia: 55, rr: 26, temp: 36.2, spo2: 90 }
  }
];

export const mockTrackedPeople = [
  { track_id: "T-A1B2", patient_id: "P-1001", position: { x: 180, y: 280 }, person_type: "patient" },
  { track_id: "T-C3D4", patient_id: "P-1002", position: { x: 420, y: 180 }, person_type: "patient" },
  { track_id: "T-E5F6", patient_id: "P-1006", position: { x: 620, y: 320 }, person_type: "patient" },
  { track_id: "T-G7H8", patient_id: null, position: { x: 300, y: 400 }, person_type: "staff" },
  { track_id: "T-I9J0", patient_id: null, position: { x: 520, y: 250 }, person_type: "unknown" },
];

export const mockZones = [
  { name: "Triage", x: 50, y: 50, width: 200, height: 150, color: "#3b82f6" },
  { name: "Waiting Room", x: 300, y: 50, width: 250, height: 200, color: "#8b5cf6" },
  { name: "Treatment Bay A", x: 50, y: 250, width: 200, height: 200, color: "#10b981" },
  { name: "Treatment Bay B", x: 300, y: 300, width: 200, height: 150, color: "#10b981" },
  { name: "Corridor", x: 550, y: 50, width: 100, height: 400, color: "#6b7280" },
];

export const mockStats = {
  total_tracked: 5,
  tagged_patients: 3,
  untagged: 2,
  staff_count: 1,
  critical_located: 2,
  urgent_located: 1,
};
