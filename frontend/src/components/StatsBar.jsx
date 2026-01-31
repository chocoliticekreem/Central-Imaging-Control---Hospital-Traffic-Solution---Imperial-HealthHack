export default function StatsBar({ stats }) {
  const items = [
    { label: "Tracked", value: stats.total_tracked, icon: "👥" },
    { label: "Enrolled", value: stats.tagged_patients, icon: "🏷️" },
    { label: "Unknown", value: stats.untagged, icon: "❓" },
    { label: "Critical", value: stats.critical_located, icon: "🔴", highlight: true },
    { label: "Urgent", value: stats.urgent_located, icon: "🟡" },
  ];

  return (
    <div className="flex gap-4 mb-6">
      {items.map((item) => (
        <div
          key={item.label}
          className={`flex-1 bg-slate-800 rounded-lg p-4 ${
            item.highlight && item.value > 0 ? "ring-2 ring-red-500" : ""
          }`}
        >
          <div className="text-2xl mb-1">{item.icon}</div>
          <div className="text-3xl font-bold">{item.value}</div>
          <div className="text-slate-400 text-sm">{item.label}</div>
        </div>
      ))}
    </div>
  );
}
