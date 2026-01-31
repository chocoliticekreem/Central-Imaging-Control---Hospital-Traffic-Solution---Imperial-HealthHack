import { useState } from "react";
import "./App.css";

import StatsBar from "./components/StatsBar";
import FloorMap from "./components/FloorMap";
import PatientList from "./components/PatientList";
import CriticalAlert from "./components/CriticalAlert";
import Sidebar from "./components/Sidebar";
import VideoFeed from "./components/VideoFeed";

import { useAegisData } from "./hooks/useAegisData";

import {
  mockPatients,
  mockTrackedPeople,
  mockStats,
} from "./data/mockData";

function App() {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedPerson, setSelectedPerson] = useState(null);
  const [useMockData, setUseMockData] = useState(false);

  const {
    patients: apiPatients,
    trackedPeople: apiTracked,
    stats: apiStats,
    floorPlan,
    loading,
    error,
    isConnected,
    enroll,
    updateVitals,
    addPerson,
    setupDemo,
    clearAll,
    refresh,
  } = useAegisData(autoRefresh ? 2000 : null);

  const patients = useMockData || !isConnected ? mockPatients : apiPatients;
  const trackedPeople = useMockData || !isConnected ? mockTrackedPeople : apiTracked;
  const stats = useMockData || !isConnected ? mockStats : apiStats;

  const handleEnroll = async (trackId, patientId) => {
    if (useMockData || !isConnected) return;
    await enroll(trackId, patientId);
  };

  const handleUpdateVitals = async (patientId, direction) => {
    if (useMockData || !isConnected) return;
    await updateVitals(patientId, direction);
  };

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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex">
      {/* Main Content */}
      <div className="flex-1 p-6 overflow-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-white flex items-center gap-2">
              <span className="text-3xl">🏥</span>
              Aegis Flow
            </h1>
            <span
              className={`px-3 py-1 rounded-full text-xs font-medium ${
                loading
                  ? "bg-blue-500/20 text-blue-400 border border-blue-500/30"
                  : isConnected
                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
                  : "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30"
              }`}
            >
              {loading ? "● Connecting..." : isConnected ? "● Live" : "○ Offline"}
            </span>
          </div>

          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-300 hover:text-white transition-colors">
              <input
                type="checkbox"
                className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-800"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              Auto Refresh
            </label>
            <label className="flex items-center gap-2 cursor-pointer text-sm text-slate-300 hover:text-white transition-colors">
              <input
                type="checkbox"
                className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-500 focus:ring-blue-500 focus:ring-offset-slate-800"
                checked={useMockData}
                onChange={(e) => setUseMockData(e.target.checked)}
              />
              Mock Data
            </label>
          </div>
        </div>

        {/* Backend not running */}
        {!loading && !isConnected && !useMockData && (
          <div className="mb-4 p-4 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-sm">
            <strong>Backend not running.</strong> Start it in a terminal:{" "}
            <code className="bg-slate-800 px-2 py-1 rounded">uvicorn aegis_flow.api:app --reload --port 8000</code>
            {" "}(from project root). Then{" "}
            <button type="button" className="underline hover:no-underline" onClick={() => refresh()}>
              retry connection
            </button>.
          </div>
        )}

        {/* Stats Bar */}
        <StatsBar stats={stats} />

        {/* Critical Alerts */}
        <CriticalAlert patients={patients} trackedPeople={trackedPeople} />

        {/* Main Grid - 2 columns */}
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-6">
          {/* Video Feed */}
          <VideoFeed isConnected={isConnected && !useMockData} />

          {/* Floor Map */}
          <FloorMap
            trackedPeople={trackedPeople}
            patients={patients}
            floorPlan={floorPlan}
            onSelectPerson={setSelectedPerson}
          />
        </div>

        {/* Patient List - Full Width */}
        <PatientList
          patients={patients}
          trackedPeople={trackedPeople}
          onSelectPatient={(p) => console.log("Selected:", p)}
        />
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
