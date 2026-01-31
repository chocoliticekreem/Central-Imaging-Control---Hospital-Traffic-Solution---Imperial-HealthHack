"""
Aegis Flow API
==============
FastAPI backend for the React frontend.

Run: uvicorn aegis_flow.api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
import cv2
import time
import threading

# Add paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aegis_flow.core.state_manager import StateManager
from aegis_flow.vision.detector import PersonDetector
from aegis_flow.vision.tracker import CentroidTracker
from aegis_flow.vision.classifier import UniformClassifier

app = FastAPI(title="Aegis Flow API", version="1.0.0")

# Global CV components (initialized lazily)
cv_components = {
    "detector": None,
    "tracker": None,
    "classifier": None,
    "camera": None,
    "lock": threading.Lock(),
    "running": False,
}

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize state manager (singleton)
sm = StateManager()
sm.floor_plan.setup_demo_zones()
sm.floor_plan.create_demo_floor_plan()


# ============================================================================
# Response Models
# ============================================================================

class PatientResponse(BaseModel):
    patient_id: str
    name: str
    chief_complaint: str
    news2_score: int
    risk_level: str
    status_color: str
    vitals: dict


class TrackedPersonResponse(BaseModel):
    track_id: str
    patient_id: Optional[str]
    position: dict
    map_position: dict
    person_type: str


class StatsResponse(BaseModel):
    total_tracked: int
    tagged_patients: int
    untagged: int
    staff_count: int
    critical_located: int
    urgent_located: int


class EnrollRequest(BaseModel):
    track_id: str
    patient_id: str


# ============================================================================
# Patient Endpoints
# ============================================================================

@app.get("/api/patients", response_model=List[PatientResponse])
def get_patients():
    """Get all patients from ELR."""
    patients = sm.elr.get_all_patients()
    return [
        PatientResponse(
            patient_id=p.patient_id,
            name=p.name,
            chief_complaint=p.chief_complaint,
            news2_score=p.news2_score,
            risk_level=p.risk_level,
            status_color=p.status_color,
            vitals={
                "hr": p.pulse,
                "bp_sys": p.systolic_bp,
                "bp_dia": 80,  # Not tracked separately
                "rr": p.respiratory_rate,
                "temp": p.temperature,
                "spo2": p.oxygen_saturation,
            }
        )
        for p in patients
    ]


@app.get("/api/patients/{patient_id}", response_model=PatientResponse)
def get_patient(patient_id: str):
    """Get a specific patient."""
    p = sm.elr.get_patient(patient_id)
    if not p:
        raise HTTPException(status_code=404, detail="Patient not found")
    return PatientResponse(
        patient_id=p.patient_id,
        name=p.name,
        chief_complaint=p.chief_complaint,
        news2_score=p.news2_score,
        risk_level=p.risk_level,
        status_color=p.status_color,
        vitals={
            "hr": p.pulse,
            "bp_sys": p.systolic_bp,
            "bp_dia": 80,
            "rr": p.respiratory_rate,
            "temp": p.temperature,
            "spo2": p.oxygen_saturation,
        }
    )


@app.get("/api/patients/risk/{risk_level}", response_model=List[PatientResponse])
def get_patients_by_risk(risk_level: str):
    """Get patients by risk level (high, medium, low)."""
    patients = sm.elr.get_patients_by_risk(risk_level)
    return [
        PatientResponse(
            patient_id=p.patient_id,
            name=p.name,
            chief_complaint=p.chief_complaint,
            news2_score=p.news2_score,
            risk_level=p.risk_level,
            status_color=p.status_color,
            vitals={
                "hr": p.pulse,
                "bp_sys": p.systolic_bp,
                "bp_dia": 80,
                "rr": p.respiratory_rate,
                "temp": p.temperature,
                "spo2": p.oxygen_saturation,
            }
        )
        for p in patients
    ]


# ============================================================================
# Tracking Endpoints
# ============================================================================

@app.get("/api/tracked", response_model=List[TrackedPersonResponse])
def get_tracked():
    """Get all currently tracked people."""
    tracked = sm.get_all_tracked()
    return [
        TrackedPersonResponse(
            track_id=p.track_id,
            patient_id=p.patient_id,
            position={"x": p.position[0], "y": p.position[1]},
            map_position={"x": p.map_position[0], "y": p.map_position[1]},
            person_type=p.person_type
        )
        for p in tracked
    ]


@app.get("/api/tracked/patients")
def get_tracked_patients():
    """Get tracked people who are enrolled as patients."""
    result = []
    for person, record in sm.get_tracked_patients():
        result.append({
            "track_id": person.track_id,
            "patient_id": person.patient_id,
            "position": {"x": person.position[0], "y": person.position[1]},
            "map_position": {"x": person.map_position[0], "y": person.map_position[1]},
            "patient": {
                "name": record.name,
                "news2_score": record.news2_score,
                "risk_level": record.risk_level,
                "status_color": record.status_color,
            }
        })
    return result


@app.get("/api/tracked/unidentified", response_model=List[TrackedPersonResponse])
def get_unidentified():
    """Get tracked people not yet enrolled."""
    unidentified = sm.get_unidentified()
    return [
        TrackedPersonResponse(
            track_id=p.track_id,
            patient_id=None,
            position={"x": p.position[0], "y": p.position[1]},
            map_position={"x": p.map_position[0], "y": p.map_position[1]},
            person_type=p.person_type
        )
        for p in unidentified
    ]


# ============================================================================
# Enrollment Endpoints
# ============================================================================

@app.post("/api/enroll")
def enroll_patient(request: EnrollRequest):
    """Link a tracked person to a patient record."""
    success = sm.enroll_patient(request.track_id, request.patient_id)
    if not success:
        raise HTTPException(status_code=400, detail="Enrollment failed - check track_id and patient_id")
    return {"success": True, "message": f"Enrolled {request.track_id} as {request.patient_id}"}


@app.delete("/api/enroll/{track_id}")
def unenroll_patient(track_id: str):
    """Remove patient link from tracked person."""
    sm.untag_patient(track_id)
    return {"success": True}


# ============================================================================
# Stats Endpoint
# ============================================================================

@app.get("/api/stats", response_model=StatsResponse)
def get_stats():
    """Get dashboard statistics."""
    stats = sm.get_stats()
    return StatsResponse(**stats)


# ============================================================================
# Demo Endpoints
# ============================================================================

@app.post("/api/demo/setup")
def demo_setup():
    """Set up demo data."""
    sm.demo_setup()
    return {"success": True, "message": "Demo data loaded"}


@app.post("/api/demo/clear")
def demo_clear():
    """Clear all tracked people."""
    sm.demo_clear_all()
    return {"success": True, "message": "Cleared all tracked people"}


@app.post("/api/demo/add-person")
def demo_add_person(camera_id: str = "cam_corridor", person_type: str = "patient"):
    """Add a demo person."""
    import random
    position = (random.randint(100, 600), random.randint(100, 400))
    person = sm.demo_add_person(camera_id, position, person_type)
    return {"success": True, "track_id": person.track_id}


@app.post("/api/demo/vitals/{patient_id}/{direction}")
def demo_update_vitals(patient_id: str, direction: str):
    """Update patient vitals (worse/better)."""
    if direction == "worse":
        sm.elr.demo_deteriorate(patient_id)
    elif direction == "better":
        sm.elr.demo_improve(patient_id)
    else:
        raise HTTPException(status_code=400, detail="Direction must be 'worse' or 'better'")
    return {"success": True}


# ============================================================================
# Video Streaming
# ============================================================================

def init_cv_components():
    """Initialize CV components if not already done."""
    with cv_components["lock"]:
        if cv_components["detector"] is None:
            print("Initializing CV components...")
            cv_components["detector"] = PersonDetector(confidence=0.5)
            cv_components["tracker"] = CentroidTracker(max_distance=80, max_missed=15)
            cv_components["classifier"] = UniformClassifier()
            print("CV components ready!")


def generate_frames():
    """Generator that yields MJPEG frames with CV processing."""
    init_cv_components()

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    detector = cv_components["detector"]
    tracker = cv_components["tracker"]
    classifier = cv_components["classifier"]

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        # Run CV pipeline
        detections = detector.detect(frame)
        tracks = tracker.update(detections)

        # Process each tracked person and update state manager
        for track_id, tracked in tracks.items():
            person_type = classifier.classify(frame, tracked.bbox)

            # Update state manager
            sm.update_tracked(
                track_id=track_id,
                camera_id="cam_webcam",
                position=tracked.centroid,
                person_type=person_type
            )

            # Draw bounding box
            x1, y1, x2, y2 = tracked.bbox

            # Color based on type
            if person_type == "staff":
                color = (255, 165, 0)  # Orange
            else:
                color = (0, 255, 0)  # Green

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Label
            label = f"{track_id} [{person_type}]"
            cv2.putText(frame, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Center dot
            cx, cy = tracked.centroid
            cv2.circle(frame, (cx, cy), 5, color, -1)

        # Encode frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

        time.sleep(0.033)  # ~30 FPS


@app.get("/api/video")
def video_feed():
    """Stream video with CV detections as MJPEG."""
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.post("/api/video/start")
def start_video():
    """Start video processing."""
    init_cv_components()
    return {"success": True, "message": "Video processing started"}


@app.post("/api/video/stop")
def stop_video():
    """Stop video processing."""
    # Note: The stream will stop when client disconnects
    return {"success": True, "message": "Video processing stopped"}


# ============================================================================
# Health Check
# ============================================================================

@app.get("/api/health")
def health_check():
    """API health check."""
    return {"status": "ok", "service": "aegis-flow"}
