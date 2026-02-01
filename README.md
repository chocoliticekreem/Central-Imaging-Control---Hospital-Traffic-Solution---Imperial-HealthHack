# CIC - Central Imaging Control

Real-time patient location and monitoring system for hospital Emergency Departments using computer vision and Re-ID tracking with NEWS2 scoring.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CIC SYSTEM                               │
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   Webcam    │───▶│   YOLO +    │───▶│   Flask Server      │  │
│  │   Feed      │    │   Re-ID     │    │   (Port 5001)       │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│                            │                     │               │
│                            ▼                     ▼               │
│                     ┌─────────────┐       ┌─────────────┐       │
│                     │  2D Map     │       │  Dashboard  │       │
│                     │  Transform  │       │  (HTML)     │       │
│                     └─────────────┘       └─────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
HealthHack/
├── cic/                      # Main package
│   ├── vision/               # Computer Vision + Flask App
│   │   ├── app_system2.py    # Main application (Flask + YOLO + Re-ID)
│   │   ├── templates/        # HTML dashboard
│   │   │   └── index2.html   # Live dashboard UI
│   │   ├── patients.json     # Mock EPR database
│   │   ├── detector.py       # YOLO wrapper
│   │   ├── tracker.py        # Centroid tracking
│   │   ├── classifier.py     # Uniform classification
│   │   └── reid.py           # Re-identification
│   ├── core/                 # Core logic
│   │   ├── entities.py       # Data classes
│   │   ├── state_manager.py  # Central state
│   │   ├── elr_mock.py       # Mock ELR with NEWS2
│   │   └── floor_plan.py     # Floor plan manager
│   ├── interface/            # Alternative Streamlit UI
│   │   └── dashboard.py      # Streamlit dashboard
│   └── requirements.txt      # Python dependencies
│
└── yolov8n.pt               # YOLO model weights
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r cic/requirements.txt
```

### 2. Run the Application

```bash
python cic/vision/app_system2.py
```

The system will:
- Open webcam feed with YOLO detection
- Start Flask server at `http://localhost:5001`
- Show 2D map with patient positions

### 3. Access Dashboard

**Local:** Open `http://localhost:5001` in your browser.

**From Phone (same WiFi):**
1. Find your computer's IP: `ipconfig getifaddr en0`
2. Open `http://<your-ip>:5001` on your phone

## Features

- **Real-time tracking**: YOLOv8 person detection with persistent tracking
- **Re-identification**: ResNet18 feature extraction for patient matching
- **Perspective transform**: Maps camera coordinates to 2D floor plan
- **Live dashboard**: MJPEG streaming + JSON API for patient data
- **EPR integration**: Links tracked patients to mock medical records

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Dashboard HTML page |
| `/data` | JSON: Current patient positions + EPR data |
| `/map_feed` | MJPEG: Live 2D map stream |

## NEWS2 Risk Levels

| Score | Risk Level | Color |
|-------|------------|-------|
| 0-4 | Low | Green |
| 5-6 | Medium | Yellow |
| 7+ | High | Red |

## Calibration

The perspective transform uses 4 calibration points defined in `app_system2.py`:
```python
src_points = np.float32([
    [817, 719],   # Top-Left
    [1441, 756],  # Top-Right
    [1664, 1072], # Bottom-Right
    [216, 1068]   # Bottom-Left
])
```

Use `calibrate_camera.py` or `calibrate_camera2.py` to recalibrate for your space.

## Configuration

Key settings in `app_system2.py`:
- `MAP_WIDTH, MAP_HEIGHT`: 2D map dimensions (default 600x600)
- `MATCH_THRESHOLD`: Re-ID similarity threshold (default 0.20)
- Flask port: 5001 (to avoid AirPlay conflict on Mac)

## License

Imperial College London HealthHack 2024
