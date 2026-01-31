import { mockZones } from "../data/mockData";

// Zone colors for backend zone names
const ZONE_COLORS = {
  "Corridor A": "#6b7280",
  "Waiting Room": "#8b5cf6",
  "Triage": "#3b82f6",
  "Treatment": "#10b981",
};

export default function FloorMap({ trackedPeople, patients, floorPlan, onSelectPerson }) {
  // Use backend floor plan when connected (800x600, same as Streamlit/code)
  const width = floorPlan?.width ?? 700;
  const height = floorPlan?.height ?? 500;
  const zones = floorPlan?.zones?.length
    ? floorPlan.zones.map((z) => ({
        id: z.camera_id,
        name: z.camera_name,
        x: z.map_x,
        y: z.map_y,
        width: z.map_width,
        height: z.map_height,
        color: ZONE_COLORS[z.camera_name] ?? "#64748b",
      }))
    : mockZones.map((z, i) => ({ ...z, id: z.name + i }));

  const getPatientInfo = (tracked) => {
    if (!tracked.patient_id) return null;
    return patients.find((p) => p.patient_id === tracked.patient_id);
  };

  const getDotColor = (tracked) => {
    const patient = getPatientInfo(tracked);
    if (patient) return patient.status_color;
    if (tracked.person_type === "staff") return "#3b82f6";
    return "#64748b";
  };

  const getDotSize = (tracked) => {
    const patient = getPatientInfo(tracked);
    if (patient?.risk_level === "high") return 18;
    if (patient?.risk_level === "medium") return 15;
    return 12;
  };

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
      <div className="p-4 border-b border-slate-700">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <span className="text-xl">🗺️</span>
          Floor Plan
        </h2>
      </div>

      <div className="p-4">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full rounded-lg bg-slate-900/50"
          preserveAspectRatio="xMidYMid meet"
        >
          <defs>
            <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
              <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#334155" strokeWidth="0.5" />
            </pattern>
          </defs>
          {/* Background: floor plan image from API or grid */}
          {floorPlan?.image_base64 ? (
            <image
              href={`data:image/png;base64,${floorPlan.image_base64}`}
              x={0}
              y={0}
              width={width}
              height={height}
              preserveAspectRatio="xMidYMid meet"
            />
          ) : (
            <rect width="100%" height="100%" fill="url(#grid)" />
          )}

          {/* Zones */}
          {zones.map((zone) => (
            <g key={zone.id ?? zone.name}>
              <rect
                x={zone.x}
                y={zone.y}
                width={zone.width}
                height={zone.height}
                fill={zone.color}
                fillOpacity={0.1}
                stroke={zone.color}
                strokeWidth={2}
                rx={12}
              />
              <text
                x={zone.x + 12}
                y={zone.y + 24}
                fill={zone.color}
                fontSize={13}
                fontWeight="600"
              >
                {zone.name}
              </text>
            </g>
          ))}

          {/* Tracked people */}
          {trackedPeople.map((tracked) => {
            const patient = getPatientInfo(tracked);
            const color = getDotColor(tracked);
            const size = getDotSize(tracked);
            const isHighRisk = patient?.risk_level === "high";

            return (
              <g
                key={tracked.track_id}
                className="cursor-pointer transition-transform hover:scale-110"
                onClick={() => onSelectPerson(tracked)}
              >
                {/* Pulse effect for high risk */}
                {isHighRisk && (
                  <>
                    <circle
                      cx={tracked.position.x}
                      cy={tracked.position.y}
                      r={size + 12}
                      fill="none"
                      stroke="#ef4444"
                      strokeWidth={2}
                      opacity={0.4}
                    >
                      <animate
                        attributeName="r"
                        values={`${size + 8};${size + 20};${size + 8}`}
                        dur="2s"
                        repeatCount="indefinite"
                      />
                      <animate
                        attributeName="opacity"
                        values="0.4;0.1;0.4"
                        dur="2s"
                        repeatCount="indefinite"
                      />
                    </circle>
                  </>
                )}

                {/* Shadow */}
                <circle
                  cx={tracked.position.x + 2}
                  cy={tracked.position.y + 2}
                  r={size}
                  fill="black"
                  opacity={0.3}
                />

                {/* Main dot */}
                <circle
                  cx={tracked.position.x}
                  cy={tracked.position.y}
                  r={size}
                  fill={color}
                  stroke="white"
                  strokeWidth={2}
                />

                {/* NEWS2 score */}
                {patient && (
                  <text
                    x={tracked.position.x}
                    y={tracked.position.y + 5}
                    textAnchor="middle"
                    fill="white"
                    fontSize={11}
                    fontWeight="bold"
                  >
                    {patient.news2_score}
                  </text>
                )}

                {/* Label */}
                <text
                  x={tracked.position.x + size + 8}
                  y={tracked.position.y + 4}
                  fill="#94a3b8"
                  fontSize={11}
                  fontWeight="500"
                >
                  {patient ? patient.patient_id : tracked.track_id}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 mt-4 text-xs text-slate-400">
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-red-500"></span> Critical
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-yellow-500"></span> Urgent
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-green-500"></span> Stable
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-blue-500"></span> Staff
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-slate-500"></span> Unknown
          </span>
        </div>
      </div>
    </div>
  );
}
