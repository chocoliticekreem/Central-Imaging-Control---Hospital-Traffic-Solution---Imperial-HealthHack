# CIC - Clinical Intelligence Center

Real-time patient location and monitoring system for hospital Emergency Departments using computer vision and NEWS2 scoring.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         REMOTE SERVER                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   FastAPI   │───▶│    State    │◀───│   Mock ELR          │  │
│  │   Backend   │    │   Manager   │    │   (Patient Data)    │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
│         │                  │                                     │
│         ▼                  ▼                                     │
│  ┌─────────────┐    ┌─────────────┐                             │
│  │  REST API   │    │  Floor Plan │                             │
│  │  /api/*     │    │   Manager   │                             │
│  └─────────────┘    └─────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
         │
         │ HTTP (API calls)
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      LOCAL WORKSTATION                           │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │   React     │───▶│   Webcam    │───▶│   CV Pipeline       │  │
│  │   Frontend  │    │   Stream    │    │   (YOLO + Tracker)  │  │
│  └─────────────┘    └─────────────┘    └─────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
HealthHack/
├── cic/                      # Backend (Python)
│   ├── api/                  # API modules
│   │   └── video.py          # Video streaming (separate for easy updates)
│   ├── core/                 # Core logic
│   │   ├── entities.py       # Data classes (Patient, TrackedPerson, etc.)
│   │   ├── state_manager.py  # Central state management
│   │   ├── elr_mock.py       # Mock ELR with NEWS2 patients
│   │   └── floor_plan.py     # Floor plan & zone mapping
│   ├── vision/               # Computer Vision
│   │   ├── detector.py       # YOLO person detection
│   │   ├── tracker.py        # Centroid tracking
│   │   ├── classifier.py     # Uniform color classification
│   │   └── reid.py           # Re-identification
│   ├── pipeline/             # CV Pipeline
│   │   ├── bridge.py         # Queue messaging
│   │   └── processor.py      # Main CV loop
│   ├── api.py                # Main FastAPI app
│   ├── config.py             # Configuration
│   └── requirements.txt      # Python dependencies
│
├── frontend/                 # Frontend (React + Vite)
│   ├── src/
│   │   ├── api/              # API client
│   │   │   └── client.js     # Fetch wrapper + endpoints
│   │   ├── components/       # React components
│   │   │   ├── VideoFeed.jsx
│   │   │   ├── FloorMap.jsx
│   │   │   ├── PatientList.jsx
│   │   │   ├── StatsBar.jsx
│   │   │   ├── CriticalAlert.jsx
│   │   │   └── Sidebar.jsx
│   │   ├── hooks/            # Custom hooks
│   │   │   └── useAegisData.js
│   │   ├── data/             # Mock data
│   │   │   └── mockData.js
│   │   └── App.jsx           # Main app
│   └── package.json
│
└── README.md
```

## Quick Start

### 1. Install Dependencies

```bash
# Backend
cd cic
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Run Backend (Remote Server)

```bash
cd cic
uvicorn api:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://<server-ip>:8000`

### 3. Run Frontend (Local)

```bash
cd frontend

# For local development
npm run dev

# For connecting to remote API server
VITE_API_URL=http://<server-ip>:8000/api npm run dev
```

### 4. Run Webcam (Local Only)

The webcam streaming runs locally. Start a local backend instance:

```bash
cd cic
uvicorn api:app --port 8000
```

Then click "Start Camera" in the frontend.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/patients` | All patients from ELR |
| GET | `/api/patients/{id}` | Single patient |
| GET | `/api/tracked` | Currently tracked people |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/floor-plan` | Floor plan + zones |
| POST | `/api/enroll` | Link tracked person to patient |
| GET | `/api/video` | MJPEG video stream |
| GET | `/api/video/status` | Camera availability |
| POST | `/api/demo/setup` | Load demo data |
| POST | `/api/demo/add-person` | Add test person |
| POST | `/api/demo/clear` | Clear all tracked |

## Configuration

### Backend (`cic/config.py`)

```python
CAMERA_INDEX = 0          # Webcam index
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
GHOST_TIMEOUT = 30        # Seconds before removing lost track
```

### Frontend Environment

Create `.env` file in `frontend/`:

```env
VITE_API_URL=http://<server-ip>:8000/api
```

## Team Development

### File Ownership

| Module | Owner | Files |
|--------|-------|-------|
| Core | - | `cic/core/*` |
| Vision | - | `cic/vision/*` |
| Video/Webcam | - | `cic/api/video.py` |
| API | - | `cic/api.py` |
| Frontend | - | `frontend/src/*` |
| ELR Mock | - | `cic/core/elr_mock.py` |
| Floor Plan | - | `cic/core/floor_plan.py` |

### Merge Strategy

- **Video code** is isolated in `cic/api/video.py` - update without affecting main API
- **Vision modules** are independent - update detector/tracker/classifier separately
- **Frontend components** are modular - update individual components

## NEWS2 Scoring

Patients are categorized by NEWS2 (National Early Warning Score 2):

| Score | Risk Level | Color |
|-------|------------|-------|
| 0-4 | Low | 🟢 Green |
| 5-6 | Medium | 🟡 Yellow |
| 7+ | High | 🔴 Red |

## Features

- **Real-time tracking**: YOLO-based person detection with centroid tracking
- **Patient identification**: Color-based uniform classification + Re-ID
- **Floor plan visualization**: SVG map with animated patient dots
- **NEWS2 integration**: Risk-based prioritization
- **Demo mode**: Injectable events for presentations
- **Offline fallback**: Mock data when backend unavailable

## License

Imperial College London HealthHack 2024
