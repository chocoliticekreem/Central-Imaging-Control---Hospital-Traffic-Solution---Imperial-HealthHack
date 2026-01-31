import { mockZones } from "../data/mockData";

export default function FloorMap({ trackedPeople, patients, onSelectPerson }) {
  const width = 700;
  const height = 500;

  // Get patient info for a tracked person
  const getPatientInfo = (tracked) => {
    if (!tracked.patient_id) return null;
    return patients.find((p) => p.patient_id === tracked.patient_id);
  };

  // Get dot color based on person type/risk
  const getDotColor = (tracked) => {
    const patient = getPatientInfo(tracked);
    if (patient) {
      return patient.status_color;
    }
    if (tracked.person_type === "staff") return "#3b82f6"; // blue
    return "#6b7280"; // gray for unknown
  };

  // Get dot size based on risk level
  const getDotSize = (tracked) => {
    const patient = getPatientInfo(tracked);
    if (patient?.risk_level === "high") return 16;
    if (patient?.risk_level === "medium") return 14;
    return 10;
  };

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <h2 className="text-xl font-semibold mb-4">📍 Floor Plan</h2>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="w-full bg-slate-900 rounded-lg"
      >
        {/* Draw zones */}
        {mockZones.map((zone) => (
          <g key={zone.name}>
            <rect
              x={zone.x}
              y={zone.y}
              width={zone.width}
              height={zone.height}
              fill={zone.color}
              fillOpacity={0.2}
              stroke={zone.color}
              strokeWidth={2}
              rx={8}
            />
            <text
              x={zone.x + 10}
              y={zone.y + 25}
              fill={zone.color}
              fontSize={14}
              fontWeight="bold"
            >
              {zone.name}
            </text>
          </g>
        ))}

        {/* Draw tracked people */}
        {trackedPeople.map((tracked) => {
          const patient = getPatientInfo(tracked);
          const color = getDotColor(tracked);
          const size = getDotSize(tracked);
          const isHighRisk = patient?.risk_level === "high";

          return (
            <g
              key={tracked.track_id}
              className="map-dot cursor-pointer"
              onClick={() => onSelectPerson(tracked)}
            >
              {/* Outer ring for high risk */}
              {isHighRisk && (
                <circle
                  cx={tracked.position.x}
                  cy={tracked.position.y}
                  r={size + 8}
                  fill="none"
                  stroke="#ef4444"
                  strokeWidth={3}
                  opacity={0.6}
                >
                  <animate
                    attributeName="r"
                    values={`${size + 5};${size + 12};${size + 5}`}
                    dur="2s"
                    repeatCount="indefinite"
                  />
                  <animate
                    attributeName="opacity"
                    values="0.6;0.2;0.6"
                    dur="2s"
                    repeatCount="indefinite"
                  />
                </circle>
              )}

              {/* Main dot */}
              <circle
                cx={tracked.position.x}
                cy={tracked.position.y}
                r={size}
                fill={color}
                stroke="white"
                strokeWidth={2}
              />

              {/* NEWS2 score for patients */}
              {patient && (
                <text
                  x={tracked.position.x}
                  y={tracked.position.y + 4}
                  textAnchor="middle"
                  fill="white"
                  fontSize={10}
                  fontWeight="bold"
                >
                  {patient.news2_score}
                </text>
              )}

              {/* Label */}
              <text
                x={tracked.position.x + size + 5}
                y={tracked.position.y + 4}
                fill="#94a3b8"
                fontSize={12}
              >
                {patient ? patient.patient_id : tracked.track_id}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="flex gap-4 mt-4 text-sm text-slate-400">
        <span>🔴 High</span>
        <span>🟡 Medium</span>
        <span>🟢 Low</span>
        <span>🔵 Staff</span>
        <span>⚫ Unknown</span>
      </div>
    </div>
  );
}
