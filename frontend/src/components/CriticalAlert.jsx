export default function CriticalAlert({ patients, trackedPeople }) {
  const criticalLocated = patients
    .filter((p) => p.risk_level === "high")
    .filter((p) => trackedPeople.some((t) => t.patient_id === p.patient_id))
    .map((patient) => {
      const tracked = trackedPeople.find((t) => t.patient_id === patient.patient_id);
      return { patient, tracked };
    });

  if (criticalLocated.length === 0) return null;

  return (
    <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-red-500/20 to-red-600/10 border border-red-500/50 backdrop-blur">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
          <span className="text-2xl animate-pulse">🚨</span>
        </div>
        <div>
          <h3 className="text-lg font-bold text-red-400">
            {criticalLocated.length} Critical Patient{criticalLocated.length > 1 ? "s" : ""} Located
          </h3>
          <p className="text-sm text-red-300/80">Immediate attention required</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {criticalLocated.map(({ patient, tracked }) => (
          <div
            key={patient.patient_id}
            className="bg-slate-900/50 rounded-lg p-3 border border-red-500/30"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold text-white">{patient.patient_id}</span>
              <span className="text-2xl font-bold text-red-400">
                {patient.news2_score}
              </span>
            </div>
            <div className="text-sm text-slate-300">{patient.name}</div>
            <div className="text-xs text-slate-400 mt-1">
              📍 ({tracked?.position?.x || 0}, {tracked?.position?.y || 0})
            </div>
            <div className="text-xs text-red-300/80 mt-1 truncate">
              {patient.chief_complaint}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
