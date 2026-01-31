"""
Aegis Flow Configuration
========================
Central configuration for all modules. Adjust these values for demo tuning.
"""

# =============================================================================
# STATE THRESHOLDS (seconds)
# =============================================================================
SAFE_THRESHOLD = 300        # 5 min - patient is safe if interacted within this time
AT_RISK_THRESHOLD = 900     # 15 min - patient becomes critical after this time

# =============================================================================
# GHOST ENTITY SETTINGS
# =============================================================================
GHOST_TIMEOUT = 30          # seconds to keep "ghost" entity after losing track
FLICKER_THRESHOLD = 5       # consecutive missed frames before considering entity lost

# =============================================================================
# INTERACTION DETECTION
# =============================================================================
INTERACTION_DISTANCE = 100  # pixels - how close staff must be to count as interaction
INTERACTION_DURATION = 3    # seconds - minimum duration to register as interaction

# =============================================================================
# UNIFORM COLOR DETECTION (HSV ranges)
# =============================================================================
# Green surgical scrubs for staff
STAFF_COLOR = {
    "h_min": 35, "h_max": 85,
    "s_min": 50, "s_max": 255,
    "v_min": 50, "v_max": 255
}

# White/gray for patients
PATIENT_COLOR = {
    "h_min": 0, "h_max": 180,
    "s_min": 0, "s_max": 50,
    "v_min": 150, "v_max": 255
}

# =============================================================================
# VISION PIPELINE
# =============================================================================
CAMERA_INDEX = 0            # webcam index (0 = default)
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
DETECTION_CONFIDENCE = 0.5  # YOLO confidence threshold
YOLO_MODEL = "yolov8n.pt"   # Use nano model for speed

# =============================================================================
# UI SETTINGS
# =============================================================================
DASHBOARD_REFRESH_RATE = 0.5  # seconds between UI updates
