import { useState } from "react";
import { getVideoStatus } from "../api/client";

export default function VideoFeed({ isConnected }) {
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState(null);

  const videoUrl = "http://localhost:8000/api/video";

  const handleToggle = async () => {
    setError(null);
    if (!isActive) {
      try {
        const status = await getVideoStatus();
        if (!status.available) {
          setError(status.message || "Camera not available");
          return;
        }
      } catch (e) {
        // Still allow trying the stream (e.g. status endpoint down but camera might work)
        setError(null);
      }
    }
    setIsActive(!isActive);
  };

  return (
    <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
          <span className="text-xl">📷</span>
          Live Feed
        </h2>
        <button
          onClick={handleToggle}
          disabled={!isConnected}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            isActive
              ? "bg-red-500 hover:bg-red-600 text-white"
              : "bg-emerald-500 hover:bg-emerald-600 text-white"
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isActive ? "Stop" : "Start"} Camera
        </button>
      </div>

      <div className="relative aspect-video bg-slate-900">
        {!isConnected ? (
          <div className="absolute inset-0 flex items-center justify-center text-slate-500">
            <div className="text-center">
              <div className="text-4xl mb-2">📡</div>
              <p>Backend not connected</p>
            </div>
          </div>
        ) : !isActive ? (
          <div className="absolute inset-0 flex items-center justify-center text-slate-500">
            <div className="text-center">
              <div className="text-4xl mb-2">🎥</div>
              <p>Click "Start Camera" to begin</p>
            </div>
          </div>
        ) : (
          <img
            src={videoUrl}
            alt="Live video feed"
            className="w-full h-full object-contain"
            onError={() => setError("Failed to load video stream")}
          />
        )}

        {error && (
          <div className="absolute bottom-4 left-4 right-4 bg-red-500/90 text-white px-4 py-3 rounded-lg text-sm whitespace-pre-wrap">
            {error}
          </div>
        )}

        {isActive && (
          <div className="absolute top-4 left-4 flex items-center gap-2 bg-black/50 px-3 py-1 rounded-full">
            <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
            <span className="text-xs text-white">LIVE</span>
          </div>
        )}
      </div>
    </div>
  );
}
