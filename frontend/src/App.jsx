import { useState } from "react";
import "./App.css";

import StatsBar from "./components/StatsBar";
import FloorMap from "./components/FloorMap";
import PatientList from "./components/PatientList";
import CriticalAlert from "./components/CriticalAlert";
import Sidebar from "./components/Sidebar";

import {
  mockPatients as initialPatients,
  mockTrackedPeople as initialTracked,
  mockStats,
} from "./data/mockData";

function App() {
  const [patients, setPatients] = useState(initialPatients);
  const [trackedPeople, setTrackedPeople] = useState(initialTracked);
  const [selectedPerson, setSelectedPerson] = useState(null);

  // Calculate live stats
  const stats = {
    total_tracked: trackedPeople.length,
    tagged_patients: trackedPeople.filter((t) => t.patient_id).length,
    untagged: trackedPeople.filter((t) => !t.patient_id).length,
    staff_count: trackedPeople.filter((t) => t.person_type === "staff").length,
    critical_located: trackedPeople.filter((t) => {
      const p = patients.find((p) => p.patient_id === t.patient_id);
      return p?.risk_level === "high";
    }).length,
    urgent_located: trackedPeople.filter((t) => {
      const p = patients.find((p) => p.patient_id === t.patient_id);
      return p?.risk_level === "medium";
    }).length,
  };

  // Handle enrollment
  const handleEnroll = (trackId, patientId) => {
    setTrackedPeople((prev) =>
      prev.map((t) =>
        t.track_id === trackId ? { ...t, patient_id: patientId } : t
      )
    );
  };

  // Handle vitals update (demo)
  const handleUpdateVitals = (patientId, direction) => {
    setPatients((prev) =>
      prev.map((p) => {
        if (p.patient_id !== patientId) return p;

        let newScore = p.news2_score + (direction === "worse" ? 2 : -2);
        newScore = Math.max(0, Math.min(12, newScore));

        let risk_level = "low";
        let status_color = "#28a745";
        if (newScore >= 7) {
          risk_level = "high";
          status_color = "#dc3545";
        } else if (newScore >= 5) {
          risk_level = "medium";
          status_color = "#ffc107";
        }

        return { ...p, news2_score: newScore, risk_level, status_color };
      })
    );
  };

  return (
    <div className="min-h-screen flex">
      {/* Main Content */}
      <div className="flex-1 p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">🏥 Aegis Flow</h1>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" className="w-4 h-4" />
              <span>📷 Webcam</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" className="w-4 h-4" />
              <span>🔄 Auto Refresh</span>
            </label>
          </div>
        </div>

        {/* Stats */}
        <StatsBar stats={stats} />

        {/* Critical Alerts */}
        <CriticalAlert patients={patients} trackedPeople={trackedPeople} />

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Floor Map */}
          <div className="lg:col-span-2">
            <FloorMap
              trackedPeople={trackedPeople}
              patients={patients}
              onSelectPerson={setSelectedPerson}
            />
          </div>

          {/* Patient List */}
          <div>
            <PatientList
              patients={patients}
              trackedPeople={trackedPeople}
              onSelectPatient={(p) => console.log("Selected:", p)}
            />
          </div>
        </div>
      </div>

      {/* Sidebar */}
      <Sidebar
        patients={patients}
        trackedPeople={trackedPeople}
        onEnroll={handleEnroll}
        onUpdateVitals={handleUpdateVitals}
      />
    </div>
  );
}

export default App;
