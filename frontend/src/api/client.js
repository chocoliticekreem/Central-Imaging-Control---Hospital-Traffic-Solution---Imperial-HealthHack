/**
 * API Client for CIC Backend
 *
 * Configuration:
 * - API_BASE: Set via environment variable VITE_API_URL or defaults to localhost
 * - VIDEO_BASE: Always localhost (webcam runs locally)
 */

// Remote API server (can be set via environment variable)
const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

// Video always runs locally (webcam on local machine)
const VIDEO_BASE = "http://localhost:8000/api/video";

// Generic fetch wrapper
async function fetchAPI(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

// ============================================================================
// Patient Endpoints
// ============================================================================

export async function getPatients() {
  return fetchAPI("/patients");
}

export async function getPatient(patientId) {
  return fetchAPI(`/patients/${patientId}`);
}

export async function getPatientsByRisk(riskLevel) {
  return fetchAPI(`/patients/risk/${riskLevel}`);
}

// ============================================================================
// Tracking Endpoints
// ============================================================================

export async function getTracked() {
  return fetchAPI("/tracked");
}

export async function getTrackedPatients() {
  return fetchAPI("/tracked/patients");
}

export async function getUnidentified() {
  return fetchAPI("/tracked/unidentified");
}

// ============================================================================
// Enrollment Endpoints
// ============================================================================

export async function enrollPatient(trackId, patientId) {
  return fetchAPI("/enroll", {
    method: "POST",
    body: JSON.stringify({ track_id: trackId, patient_id: patientId }),
  });
}

export async function unenrollPatient(trackId) {
  return fetchAPI(`/enroll/${trackId}`, {
    method: "DELETE",
  });
}

// ============================================================================
// Stats & Floor Plan Endpoints
// ============================================================================

export async function getStats() {
  return fetchAPI("/stats");
}

export async function getFloorPlan() {
  return fetchAPI("/floor-plan");
}

// ============================================================================
// Video Endpoints (Local Only)
// ============================================================================

export function getVideoStreamUrl() {
  return VIDEO_BASE;
}

export async function getVideoStatus() {
  const response = await fetch(`${VIDEO_BASE}/status`);
  if (!response.ok) {
    throw new Error(`Video API Error: ${response.status}`);
  }
  return response.json();
}

// ============================================================================
// Demo Endpoints
// ============================================================================

export async function demoSetup() {
  return fetchAPI("/demo/setup", { method: "POST" });
}

export async function demoClear() {
  return fetchAPI("/demo/clear", { method: "POST" });
}

export async function demoAddPerson(cameraId = "cam_corridor", personType = "patient") {
  return fetchAPI(`/demo/add-person?camera_id=${cameraId}&person_type=${personType}`, {
    method: "POST",
  });
}

export async function demoUpdateVitals(patientId, direction) {
  return fetchAPI(`/demo/vitals/${patientId}/${direction}`, {
    method: "POST",
  });
}

// ============================================================================
// Health Check
// ============================================================================

export async function healthCheck() {
  return fetchAPI("/health");
}

// Export base URLs for components that need them directly
export { API_BASE, VIDEO_BASE };
