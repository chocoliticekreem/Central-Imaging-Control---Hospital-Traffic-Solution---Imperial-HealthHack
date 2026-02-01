"""
Video Streaming Module
======================
Separate module for webcam/video streaming.
Can be updated independently without affecting main API.

Run webcam locally while API runs on remote server.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import cv2
import threading
import time

# Optional CV imports (may not be available on all systems)
try:
    from cic.vision.detector import PersonDetector
    from cic.vision.tracker import CentroidTracker
    from cic.vision.classifier import UniformClassifier
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False

router = APIRouter(prefix="/api/video", tags=["video"])

# Global camera state
camera = None
camera_lock = threading.Lock()
cv_components = None


def init_cv_components():
    """Initialize CV components (detector, tracker, classifier)."""
    global cv_components
    if not CV_AVAILABLE:
        return None

    try:
        cv_components = {
            "detector": PersonDetector(),
            "tracker": CentroidTracker(max_disappeared=30),
            "classifier": UniformClassifier(),
        }
        return cv_components
    except Exception as e:
        print(f"Failed to initialize CV components: {e}")
        return None


def generate_frames():
    """Generator function for MJPEG video stream with CV overlay."""
    global camera, cv_components

    with camera_lock:
        if camera is None:
            camera = cv2.VideoCapture(0)
            camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # Initialize CV if not already done
    if cv_components is None and CV_AVAILABLE:
        init_cv_components()

    while True:
        success, frame = camera.read()
        if not success:
            break

        # Apply CV processing if available
        if cv_components:
            try:
                # Detect people
                detections = cv_components["detector"].detect(frame)

                # Update tracker
                objects = cv_components["tracker"].update(detections)

                # Draw bounding boxes and IDs
                for track_id, centroid in objects.items():
                    # Find corresponding detection for bounding box
                    for det in detections:
                        x1, y1, x2, y2 = det["bbox"]
                        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                        if abs(cx - centroid[0]) < 50 and abs(cy - centroid[1]) < 50:
                            # Classify person type
                            person_type = cv_components["classifier"].classify(frame, det["bbox"])

                            # Color based on type
                            color = (0, 255, 0) if person_type == "staff" else (255, 165, 0)

                            # Draw box
                            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

                            # Draw ID label
                            label = f"ID:{track_id} ({person_type})"
                            cv2.putText(frame, label, (x1, y1 - 10),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                            break
            except Exception as e:
                # If CV fails, just show raw frame
                cv2.putText(frame, f"CV Error: {str(e)[:30]}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Add timestamp
        timestamp = time.strftime("%H:%M:%S")
        cv2.putText(frame, timestamp, (frame.shape[1] - 100, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@router.get("/status")
def video_status():
    """Check camera availability."""
    global camera

    try:
        with camera_lock:
            if camera is None:
                test_cam = cv2.VideoCapture(0)
                available = test_cam.isOpened()
                test_cam.release()
            else:
                available = camera.isOpened()

        return {
            "available": available,
            "cv_available": CV_AVAILABLE,
            "message": "Camera ready" if available else "No camera found"
        }
    except Exception as e:
        return {
            "available": False,
            "cv_available": CV_AVAILABLE,
            "message": str(e)
        }


@router.get("")
def video_feed():
    """MJPEG video stream endpoint."""
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@router.post("/stop")
def stop_camera():
    """Stop and release the camera."""
    global camera

    with camera_lock:
        if camera is not None:
            camera.release()
            camera = None

    return {"success": True, "message": "Camera stopped"}
