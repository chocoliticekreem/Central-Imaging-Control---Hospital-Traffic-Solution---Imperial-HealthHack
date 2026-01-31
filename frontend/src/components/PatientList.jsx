export default function PatientList({ patients, trackedPeople, onSelectPatient }) {
  // Group by risk level
  const byRisk = {
    high: patients.filter((p) => p.risk_level === "high"),
    medium: patients.filter((p) => p.risk_level === "medium"),
    low: patients.filter((p) => p.risk_level === "low"),
  };

  // Check if patient is currently tracked
  const isLocated = (patientId) => {
    return trackedPeople.some((t) => t.patient_id === patientId);
  };

  const RiskSection = ({ level, icon, patients, defaultOpen }) => {
    if (patients.length === 0) return null;

    const colors = {
      high: "border-red-500 bg-red-500/10",
      medium: "border-yellow-500 bg-yellow-500/10",
      low: "border-green-500 bg-green-500/10",
    };

    return (
      <div className={`border-l-4 ${colors[level]} rounded-r-lg mb-4`}>
        <div className="p-3">
          <h3 className="font-semibold mb-2">
            {icon} {level.toUpperCase()} ({patients.length})
          </h3>
          <div className="space-y-2">
            {patients.map((patient) => (
              <div
                key={patient.patient_id}
                className="patient-card bg-slate-700/50 rounded p-3 cursor-pointer hover:bg-slate-700"
                onClick={() => onSelectPatient(patient)}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <span className="font-medium">{patient.patient_id}</span>
                    <span className="text-slate-400 ml-2">{patient.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {isLocated(patient.patient_id) ? (
                      <span className="text-green-400">📍</span>
                    ) : (
                      <span className="text-slate-500">❓</span>
                    )}
                    <span
                      className={`text-lg font-bold ${
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
                </div>
                <div className="text-sm text-slate-400 mt-1">
                  {patient.chief_complaint}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <h2 className="text-xl font-semibold mb-4">📋 Patients</h2>
      <RiskSection level="high" icon="🔴" patients={byRisk.high} defaultOpen />
      <RiskSection level="medium" icon="🟡" patients={byRisk.medium} defaultOpen />
      <RiskSection level="low" icon="🟢" patients={byRisk.low} />
    </div>
  );
}
