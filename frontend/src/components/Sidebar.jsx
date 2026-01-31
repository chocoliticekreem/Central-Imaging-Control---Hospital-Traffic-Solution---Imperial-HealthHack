import { useState, useEffect } from "react";

export default function Sidebar({
  patients,
  trackedPeople,
  onEnroll,
  onUpdateVitals,
  onAddPerson,
  onSetupDemo,
  onClearAll,
  isConnected,
}) {
  const [selectedTrack, setSelectedTrack] = useState("");
  const [selectedPatient, setSelectedPatient] = useState("");
  const [vitalsPatient, setVitalsPatient] = useState("");

  useEffect(() => {
    if (patients.length > 0 && !vitalsPatient) {
      setVitalsPatient(patients[0].patient_id);
    }
  }, [patients, vitalsPatient]);

  const unidentified = trackedPeople.filter(
    (t) => !t.patient_id && t.person_type !== "staff"
  );

  const enrolledIds = trackedPeople
    .filter((t) => t.patient_id)
    .map((t) => t.patient_id);
  const availablePatients = patients.filter(
    (p) => !enrolledIds.includes(p.patient_id)
  );

  const currentPatient = patients.find((p) => p.patient_id === vitalsPatient);

  const handleEnroll = async () => {
    if (selectedTrack && selectedPatient) {
      await onEnroll(selectedTrack, selectedPatient);
      setSelectedTrack("");
      setSelectedPatient("");
    }
  };

  return (
    <div className="w-80 bg-slate-900/50 backdrop-blur border-l border-slate-700 p-4 space-y-4 overflow-y-auto">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-700">
        <h2 className="text-lg font-bold text-white">Controls</h2>
        <span
          className={`px-2 py-1 rounded-full text-xs font-medium ${
            isConnected
              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
              : "bg-yellow-500/20 text-yellow-400 border border-yellow-500/30"
          }`}
        >
          {isConnected ? "● Live" : "○ Mock"}
        </span>
      </div>

      {/* Enrollment */}
      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <span>🏷️</span> Enrollment
        </h3>

        {unidentified.length === 0 ? (
          <div className="text-emerald-400 text-sm flex items-center gap-2">
            <span>✓</span> All patients enrolled
          </div>
        ) : (
          <div className="space-y-3">
            <div className="text-yellow-400 text-sm">
              {unidentified.length} unidentified
            </div>

            <select
              className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2.5 text-sm text-white focus:border-blue-500 focus:outline-none"
              value={selectedTrack}
              onChange={(e) => setSelectedTrack(e.target.value)}
            >
              <option value="">Select person...</option>
              {unidentified.map((t) => (
                <option key={t.track_id} value={t.track_id}>
                  {t.track_id}
                </option>
              ))}
            </select>

            <select
              className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2.5 text-sm text-white focus:border-blue-500 focus:outline-none"
              value={selectedPatient}
              onChange={(e) => setSelectedPatient(e.target.value)}
            >
              <option value="">Select patient...</option>
              {availablePatients.map((p) => (
                <option key={p.patient_id} value={p.patient_id}>
                  {p.patient_id}: {p.name}
                </option>
              ))}
            </select>

            <button
              className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg p-2.5 text-sm font-medium transition-colors"
              onClick={handleEnroll}
              disabled={!selectedTrack || !selectedPatient}
            >
              Enroll Patient
            </button>
          </div>
        )}
      </div>

      {/* Vitals */}
      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <span>💉</span> Vitals Monitor
        </h3>

        {patients.length === 0 ? (
          <div className="text-slate-400 text-sm">No patients loaded</div>
        ) : (
          <>
            <select
              className="w-full bg-slate-700 border border-slate-600 rounded-lg p-2.5 text-sm text-white focus:border-blue-500 focus:outline-none mb-4"
              value={vitalsPatient}
              onChange={(e) => setVitalsPatient(e.target.value)}
            >
              {patients.map((p) => (
                <option key={p.patient_id} value={p.patient_id}>
                  {p.patient_id}: {p.name}
                </option>
              ))}
            </select>

            {currentPatient && (
              <>
                {/* NEWS2 Display */}
                <div
                  className="text-center py-6 rounded-xl mb-4 border"
                  style={{
                    backgroundColor: currentPatient.status_color + "15",
                    borderColor: currentPatient.status_color + "40",
                  }}
                >
                  <div
                    className="text-5xl font-bold"
                    style={{ color: currentPatient.status_color }}
                  >
                    {currentPatient.news2_score}
                  </div>
                  <div className="text-slate-400 text-sm mt-2">
                    NEWS2 • {currentPatient.risk_level.toUpperCase()}
                  </div>
                </div>

                {/* Vitals Grid */}
                {currentPatient.vitals && (
                  <div className="grid grid-cols-2 gap-2 mb-4">
                    {[
                      { label: "HR", value: `${currentPatient.vitals.hr}`, unit: "bpm" },
                      { label: "BP", value: `${currentPatient.vitals.bp_sys}/${currentPatient.vitals.bp_dia}`, unit: "" },
                      { label: "SpO2", value: `${currentPatient.vitals.spo2}`, unit: "%" },
                      { label: "Temp", value: `${currentPatient.vitals.temp}`, unit: "°C" },
                    ].map((vital) => (
                      <div
                        key={vital.label}
                        className="bg-slate-700/50 rounded-lg p-2.5 text-center"
                      >
                        <div className="text-xs text-slate-400">{vital.label}</div>
                        <div className="text-white font-semibold">
                          {vital.value}
                          <span className="text-xs text-slate-400 ml-0.5">
                            {vital.unit}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Demo Buttons */}
                <div className="grid grid-cols-2 gap-2">
                  <button
                    className="bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 text-red-400 rounded-lg p-2 text-sm font-medium transition-colors disabled:opacity-50"
                    onClick={() => onUpdateVitals(vitalsPatient, "worse")}
                    disabled={!isConnected}
                  >
                    ↑ Deteriorate
                  </button>
                  <button
                    className="bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30 text-emerald-400 rounded-lg p-2 text-sm font-medium transition-colors disabled:opacity-50"
                    onClick={() => onUpdateVitals(vitalsPatient, "better")}
                    disabled={!isConnected}
                  >
                    ↓ Improve
                  </button>
                </div>
              </>
            )}
          </>
        )}
      </div>

      {/* Demo Controls */}
      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700">
        <h3 className="font-semibold text-white mb-3 flex items-center gap-2">
          <span>🎮</span> Demo Controls
        </h3>
        <div className="space-y-2">
          <button
            className="w-full bg-purple-500/20 hover:bg-purple-500/30 border border-purple-500/30 text-purple-400 rounded-lg p-2.5 text-sm font-medium transition-colors disabled:opacity-50"
            onClick={onSetupDemo}
            disabled={!isConnected}
          >
            Load Demo Data
          </button>
          <button
            className="w-full bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg p-2.5 text-sm font-medium transition-colors disabled:opacity-50"
            onClick={onAddPerson}
            disabled={!isConnected}
          >
            + Add Person
          </button>
          <button
            className="w-full bg-red-500/10 hover:bg-red-500/20 border border-red-500/20 text-red-400 rounded-lg p-2.5 text-sm font-medium transition-colors disabled:opacity-50"
            onClick={onClearAll}
            disabled={!isConnected}
          >
            Clear All
          </button>
        </div>
        {!isConnected && (
          <p className="text-xs text-slate-500 mt-3 text-center">
            Start backend to enable controls
          </p>
        )}
      </div>
    </div>
  );
}
