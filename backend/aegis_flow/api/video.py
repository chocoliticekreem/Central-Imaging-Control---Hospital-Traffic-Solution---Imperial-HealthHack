"""
Video Streaming Module
======================
Handles webcam streaming with CV processing.
Separated from main API to avoid merge conflicts with vision team.
"""

import cv2
import time
import threading
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

# Lazy imports to avoid circular dependencies
_cv_components = {
    "detector": None,
    "tracker": None,
    "classifier": None,
    "lock": threading.Lock(),
}


def _get_config():
    """Get config module."""
    try:
        from aegis_flow import config
        return config
    except ImportError:
        import config
        return config


def _get_state_manager():
    """Get shared StateManager instance."""
    from aegis_flow.core.state_manager import StateManager
    return StateManager()


def _init_cv_components():
    """Initialize CV components if not already done."""
    with _cv_components["lock"]:
        if _cv_components["detector"] is None:
            from aegis_flow.vision.detector import PersonDetector
            from aegis_flow.vision.tracker import CentroidTracker
            from aegis_flow.vision.classifier import UniformClassifier

            print("Initializing CV components...")
            _cv_components["detector"] = PersonDetector(confidence=0.5)
            _cv_components["tracker"] = CentroidTracker(max_distance=80, max_missed=15)
            _cv_components["classifier"] = UniformClassifier()
            print("CV components ready!")


def _open_camera():
    """Open default or fallback camera. Returns (cap, error_message)."""
    config = _get_config()
    idx = getattr(config, "CAMERA_INDEX", 0)
    cap = cv2.VideoCapture(idx)
    if not cap.isOpened() and idx == 0:
        cap.release()
        cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        cap.release()
        return None, (
            "Camera not available. Grant Camera permission to Terminal/Cursor in "
            "System Settings → Privacy & Security → Camera. Close other apps using the webcam."
        )
    return cap, None


def _error_frame_jpeg(message: str) -> bytes:
    """Generate a JPEG frame with error text."""
    import numpy as np
    img = np.zeros((240, 640, 3), dtype=np.uint8)
    img[:] = (60, 60, 80)
    font = cv2.FONT_HERSHEY_SIMPLEX
    for i, line in enumerate(message.split(". ")[:3]):
        cv2.putText(img, line[:50], (20, 80 + i * 50), font, 0.6, (255, 255, 255), 2)
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return buf.tobytes()


def generate_frames():
    """Generator that yields MJPEG frames with CV processing."""
    _init_cv_components()
    sm = _get_state_manager()

    cap, err = _open_camera()
    if cap is None:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + _error_frame_jpeg(err) + b'\r\n')
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    detector = _cv_components["detector"]
    tracker = _cv_components["tracker"]
    classifier = _cv_components["classifier"]

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            # Run CV pipeline
            detections = detector.detect(frame)
            tracks = tracker.update(detections)

            # Process each tracked person
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
                color = (255, 165, 0) if person_type == "staff" else (0, 255, 0)
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
    finally:
        cap.release()


# Create router for video endpoints
router = APIRouter(prefix="/api/video", tags=["video"])


@router.get("/status")
def video_status():
    """Check if the camera can be opened."""
    cap, err = _open_camera()
    if cap is not None:
        cap.release()
        return {"available": True, "message": "Camera OK"}
    return {"available": False, "message": err}


@router.get("")
def video_feed():
    """Stream video with CV detections as MJPEG."""
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
