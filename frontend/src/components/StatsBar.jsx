export default function StatsBar({ stats }) {
  const items = [
    { label: "Tracked", value: stats.total_tracked, icon: "👥", color: "text-blue-400" },
    { label: "Enrolled", value: stats.tagged_patients, icon: "🏷️", color: "text-emerald-400" },
    { label: "Unknown", value: stats.untagged, icon: "❓", color: "text-slate-400" },
    { label: "Critical", value: stats.critical_located, icon: "🔴", color: "text-red-400", highlight: true },
    { label: "Urgent", value: stats.urgent_located, icon: "🟡", color: "text-yellow-400" },
  ];

  return (
    <div className="grid grid-cols-5 gap-3 mb-6">
      {items.map((item) => (
        <div
          key={item.label}
          className={`bg-slate-800/50 backdrop-blur rounded-xl p-4 border transition-all ${
            item.highlight && item.value > 0
              ? "border-red-500/50 shadow-lg shadow-red-500/10"
              : "border-slate-700/50 hover:border-slate-600"
          }`}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">{item.icon}</span>
            <span className={`text-3xl font-bold ${item.color}`}>
              {item.value}
            </span>
          </div>
          <div className="text-slate-400 text-sm font-medium">{item.label}</div>
        </div>
      ))}
    </div>
  );
}
