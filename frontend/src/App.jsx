import { useState } from "react";
import "./App.css";

import StatsBar from "./components/StatsBar";
import FloorMap from "./components/FloorMap";
import PatientList from "./components/PatientList";
import CriticalAlert from "./components/CriticalAlert";
import Sidebar from "./components/Sidebar";

import { useAegisData } from "./hooks/useAegisData";

// Fallback mock data (used when backend is unavailable)
import {
  mockPatients,
  mockTrackedPeople,
  mockStats,
} from "./data/mockData";

function App() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [useMockData, setUseMockData] = useState(false);

  // Fetch data from backend (polls every 2 seconds when autoRefresh is on)
  const {
    patients: apiPatients,
    trackedPeople: apiTracked,
    stats: apiStats,
    loading,
    error,
    isConnected,
    enroll,
    updateVitals,
    addPerson,
    setupDemo,
    clearAll,
  } = useAegisData(autoRefresh ? 2000 : null);

  // Use mock data if backend unavailable or user toggles mock mode
  const patients = useMockData || !isConnected ? mockPatients : apiPatients;
  const trackedPeople = useMockData || !isConnected ? mockTrackedPeople : apiTracked;
  const stats = useMockData || !isConnected ? mockStats : apiStats;

  // Handle enrollment
  const handleEnroll = async (trackId, patientId) => {
    if (useMockData || !isConnected) {
      // Mock mode: just log
      console.log("Mock enroll:", trackId, patientId);
      return;
    }
    await enroll(trackId, patientId);
  };

  // Handle vitals update
  const handleUpdateVitals = async (patientId, direction) => {
    if (useMockData || !isConnected) {
      console.log("Mock vitals update:", patientId, direction);
      return;
    }
    await updateVitals(patientId, direction);
  };

  // Handle demo actions
  const handleAddPerson = async () => {
    if (useMockData || !isConnected) return;
    await addPerson("cam_corridor", "patient");
  };

  const handleSetupDemo = async () => {
    if (useMockData || !isConnected) return;
    await setupDemo();
  };

  const handleClearAll = async () => {
    if (useMockData || !isConnected) return;
    await clearAll();
  };

  return (
    <div className="min-h-screen flex">
      {/* Main Content */}
      <div className="flex-1 p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center gap-4">
            <h1 className="text-3xl font-bold">🏥 Aegis Flow</h1>
            {/* Connection status */}
            <span
              className={`px-2 py-1 rounded text-xs ${
                isConnected
                  ? "bg-green-600 text-white"
                  : "bg-yellow-600 text-white"
              }`}
            >
              {loading ? "Connecting..." : isConnected ? "Live" : "Offline (Mock)"}
            </span>
          </div>

          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="w-4 h-4"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              <span>🔄 Auto Refresh</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                className="w-4 h-4"
                checked={useMockData}
                onChange={(e) => setUseMockData(e.target.checked)}
              />
              <span>🧪 Mock Data</span>
            </label>
          </div>
        </div>

        {/* Error banner */}
        {error && !useMockData && (
          <div className="bg-yellow-900/50 border border-yellow-500 rounded-lg p-3 mb-4 text-sm">
            ⚠️ Backend unavailable: {error}. Showing mock data.
            <button
              className="ml-2 underline"
              onClick={() => setUseMockData(true)}
            >
              Use mock mode
            </button>
          </div>
        )}

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
        onAddPerson={handleAddPerson}
        onSetupDemo={handleSetupDemo}
        onClearAll={handleClearAll}
        isConnected={isConnected && !useMockData}
      />
    </div>
  );
}

export default App;
