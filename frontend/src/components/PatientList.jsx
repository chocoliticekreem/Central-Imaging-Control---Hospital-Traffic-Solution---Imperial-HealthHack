export default function PatientList({ patients, trackedPeople, onSelectPatient }) {
  const byRisk = {
    high: patients.filter((p) => p.risk_level === "high"),
    medium: patients.filter((p) => p.risk_level === "medium"),
    low: patients.filter((p) => p.risk_level === "low"),
  };

  const isLocated = (patientId) => {
    return trackedPeople.some((t) => t.patient_id === patientId);
  };

  const RiskSection = ({ level, patients }) => {
    if (patients.length === 0) return null;

    const config = {
      high: { label: "Critical", color: "red", icon: "🔴" },
      medium: { label: "Urgent", color: "yellow", icon: "🟡" },
      low: { label: "Stable", color: "green", icon: "🟢" },
    }[level];

    return (
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <span>{config.icon}</span>
          <span className="text-sm font-semibold text-slate-300">
            {config.label}
          </span>
          <span className="text-xs text-slate-500">({patients.length})</span>
        </div>
        <div className="space-y-2">
          {patients.map((patient) => (
            <div
              key={patient.patient_id}
              onClick={() => onSelectPatient(patient)}
              className={`p-3 rounded-lg cursor-pointer transition-all border ${
                level === "high"
                  ? "bg-red-500/10 border-red-500/30 hover:border-red-500/50"
                  : level === "medium"
                  ? "bg-yellow-500/10 border-yellow-500/30 hover:border-yellow-500/50"
                  : "bg-slate-700/30 border-slate-600/30 hover:border-slate-500/50"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {isLocated(patient.patient_id) ? (
                    <span className="text-emerald-400 text-sm">📍</span>
                  ) : (
                    <span className="text-slate-500 text-sm">❓</span>
                  )}
                  <span className="font-medium text-white">
                    {patient.patient_id}
                  </span>
                </div>
                <span
                  className={`text-xl font-bold ${
                    level === "high"
                      ? "text-red-400"
                      : level === "medium"
                      ? "text-yellow-400"
                      : "text-green-400"
                  }`}
                >
                  {patient.news2_score}
                </span>
              </div>
              <div className="text-sm text-slate-400 mt-1">{patient.name}</div>
              <div className="text-xs text-slate-500 mt-0.5 truncate">
                {patient.chief_complaint}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden h-full">
      <div className="p-4 border-b border-slate-700">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <span className="text-xl">📋</span>
          Patients
        </h2>
      </div>
      <div className="p-4 overflow-y-auto max-h-[500px]">
        <RiskSection level="high" patients={byRisk.high} />
        <RiskSection level="medium" patients={byRisk.medium} />
        <RiskSection level="low" patients={byRisk.low} />
      </div>
    </div>
  );
}
