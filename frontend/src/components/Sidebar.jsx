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

  // Update vitalsPatient when patients change
  useEffect(() => {
    if (patients.length > 0 && !vitalsPatient) {
      setVitalsPatient(patients[0].patient_id);
    }
  }, [patients, vitalsPatient]);

  // Get unidentified people (not staff, not enrolled)
  const unidentified = trackedPeople.filter(
    (t) => !t.patient_id && t.person_type !== "staff"
  );

  // Get patients not yet enrolled
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
    <div className="w-80 bg-slate-800 p-4 space-y-6 overflow-y-auto">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold">⚙️ Controls</h2>
        {!isConnected && (
          <span className="text-xs bg-yellow-600 px-2 py-1 rounded">Mock</span>
        )}
      </div>

      {/* Enrollment Panel */}
      <div className="bg-slate-700 rounded-lg p-4">
        <h3 className="font-semibold mb-3">🏷️ Enrollment</h3>

        {unidentified.length === 0 ? (
          <div className="text-green-400 text-sm">✓ All enrolled</div>
        ) : (
          <>
            <div className="text-yellow-400 text-sm mb-3">
              {unidentified.length} unidentified
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-sm text-slate-400">Person</label>
                <select
                  className="w-full bg-slate-600 rounded p-2 mt-1"
                  value={selectedTrack}
                  onChange={(e) => setSelectedTrack(e.target.value)}
                >
                  <option value="">Select...</option>
                  {unidentified.map((t) => (
                    <option key={t.track_id} value={t.track_id}>
                      {t.track_id}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-sm text-slate-400">Patient</label>
                <select
                  className="w-full bg-slate-600 rounded p-2 mt-1"
                  value={selectedPatient}
                  onChange={(e) => setSelectedPatient(e.target.value)}
                >
                  <option value="">Select...</option>
                  {availablePatients.map((p) => (
                    <option key={p.patient_id} value={p.patient_id}>
                      {p.patient_id}: {p.name}
                    </option>
                  ))}
                </select>
              </div>

              <button
                className="w-full bg-blue-600 hover:bg-blue-700 rounded p-2 font-semibold disabled:opacity-50"
                onClick={handleEnroll}
                disabled={!selectedTrack || !selectedPatient}
              >
                ✓ Enroll
              </button>
            </div>
          </>
        )}
      </div>

      {/* Vitals Panel */}
      <div className="bg-slate-700 rounded-lg p-4">
        <h3 className="font-semibold mb-3">💉 Vitals</h3>

        {patients.length === 0 ? (
          <div className="text-slate-400 text-sm">No patients loaded</div>
        ) : (
          <>
            <select
              className="w-full bg-slate-600 rounded p-2 mb-4"
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
                {/* Big NEWS2 display */}
                <div
                  className="text-center py-4 rounded-lg mb-4"
                  style={{ backgroundColor: currentPatient.status_color + "33" }}
                >
                  <div
                    className="text-5xl font-bold"
                    style={{ color: currentPatient.status_color }}
                  >
                    {currentPatient.news2_score}
                  </div>
                  <div className="text-slate-400 text-sm mt-1">
                    NEWS2 Score - {currentPatient.risk_level.toUpperCase()} risk
                  </div>
                </div>

                {/* Vitals grid */}
                {currentPatient.vitals && (
                  <div className="grid grid-cols-2 gap-2 text-sm mb-4">
                    <div className="bg-slate-600 rounded p-2">
                      <div className="text-slate-400">HR</div>
                      <div className="font-semibold">
                        {currentPatient.vitals.hr} bpm
                      </div>
                    </div>
                    <div className="bg-slate-600 rounded p-2">
                      <div className="text-slate-400">BP</div>
                      <div className="font-semibold">
                        {currentPatient.vitals.bp_sys}/{currentPatient.vitals.bp_dia}
                      </div>
                    </div>
                    <div className="bg-slate-600 rounded p-2">
                      <div className="text-slate-400">SpO2</div>
                      <div className="font-semibold">
                        {currentPatient.vitals.spo2}%
                      </div>
                    </div>
                    <div className="bg-slate-600 rounded p-2">
                      <div className="text-slate-400">Temp</div>
                      <div className="font-semibold">
                        {currentPatient.vitals.temp}°C
                      </div>
                    </div>
                  </div>
                )}

                {/* Demo buttons */}
                <div className="grid grid-cols-2 gap-2">
                  <button
                    className="bg-red-600 hover:bg-red-700 rounded p-2 text-sm disabled:opacity-50"
                    onClick={() => onUpdateVitals(vitalsPatient, "worse")}
                    disabled={!isConnected}
                  >
                    ⬆️ Worse
                  </button>
                  <button
                    className="bg-green-600 hover:bg-green-700 rounded p-2 text-sm disabled:opacity-50"
                    onClick={() => onUpdateVitals(vitalsPatient, "better")}
                    disabled={!isConnected}
                  >
                    ⬇️ Better
                  </button>
                </div>
              </>
            )}
          </>
        )}
      </div>

      {/* Demo Controls */}
      <div className="bg-slate-700 rounded-lg p-4">
        <h3 className="font-semibold mb-3">🎮 Demo</h3>
        <div className="space-y-2">
          <button
            className="w-full bg-purple-600 hover:bg-purple-700 rounded p-2 text-sm disabled:opacity-50"
            onClick={onSetupDemo}
            disabled={!isConnected}
          >
            🎲 Add Demo Data
          </button>
          <button
            className="w-full bg-slate-600 hover:bg-slate-500 rounded p-2 text-sm disabled:opacity-50"
            onClick={onAddPerson}
            disabled={!isConnected}
          >
            ➕ Add Person
          </button>
          <button
            className="w-full bg-red-900 hover:bg-red-800 rounded p-2 text-sm disabled:opacity-50"
            onClick={onClearAll}
            disabled={!isConnected}
          >
            🗑️ Clear All
          </button>
        </div>
        {!isConnected && (
          <p className="text-xs text-slate-500 mt-2">
            Start backend to enable demo controls
          </p>
        )}
      </div>
    </div>
  );
}
