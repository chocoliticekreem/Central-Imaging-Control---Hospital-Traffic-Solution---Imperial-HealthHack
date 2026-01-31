export default function CriticalAlert({ patients, trackedPeople }) {
  // Find critical patients who are being tracked
  const criticalLocated = patients
    .filter((p) => p.risk_level === "high")
    .filter((p) => trackedPeople.some((t) => t.patient_id === p.patient_id))
    .map((patient) => {
      const tracked = trackedPeople.find((t) => t.patient_id === patient.patient_id);
      return { patient, tracked };
    });

  if (criticalLocated.length === 0) return null;

  return (
    <div className="bg-red-900/50 border border-red-500 rounded-lg p-4 mb-6 pulse-critical">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-2xl">🚨</span>
        <span className="font-bold text-lg">
          {criticalLocated.length} CRITICAL PATIENT(S) - Immediate attention required!
        </span>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {criticalLocated.map(({ patient, tracked }) => (
          <div key={patient.patient_id} className="bg-red-950/50 rounded p-3">
            <div className="font-semibold">
              {patient.patient_id}: {patient.name}
            </div>
            <div className="text-sm text-red-200">
              📍 Position: ({tracked.position.x}, {tracked.position.y})
            </div>
            <div className="text-sm text-red-200">
              NEWS2: <span className="font-bold">{patient.news2_score}</span>
            </div>
            <div className="text-sm text-red-300 italic mt-1">
              {patient.chief_complaint}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
