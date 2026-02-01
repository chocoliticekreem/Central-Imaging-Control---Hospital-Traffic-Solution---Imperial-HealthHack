# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

**CIC (Clinical Intelligence Center)** - Patient location system for hospital EDs using CCTV + Re-ID tracking with NEWS2 scoring.

**Key insight:** NHS ELR tells WHO needs help. CIC tells WHERE they are.

## Architecture

```
Remote Server (API)          Local Workstation (Webcam)
┌─────────────────┐          ┌─────────────────┐
│  FastAPI        │◀────────▶│  React Frontend │
│  State Manager  │          │  Video Stream   │
│  Mock ELR       │          │  CV Pipeline    │
└─────────────────┘          └─────────────────┘
```

## Tech Stack

- **Backend**: FastAPI, Python
- **Frontend**: React + Vite + Tailwind
- **CV**: YOLOv8, OpenCV, Centroid Tracker
- **Patient Data**: Mock ELR with NEWS2 scoring

## Quick Start

```bash
# Backend (remote or local)
cd cic
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run dev

# With remote API
VITE_API_URL=http://<server-ip>:8000/api npm run dev
```

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `cic/core/` | State management, entities, ELR mock |
| `cic/vision/` | YOLO detector, tracker, classifier |
| `cic/api/` | Video streaming module (separate) |
| `cic/api.py` | Main FastAPI endpoints |
| `frontend/src/` | React components + hooks |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/patients` | All patients from ELR |
| `/api/tracked` | Currently tracked people |
| `/api/stats` | Dashboard statistics |
| `/api/floor-plan` | Floor plan + zones |
| `/api/enroll` | Link person → patient |
| `/api/video` | MJPEG stream (local only) |

## NEWS2 Risk Levels

| Score | Risk | Color |
|-------|------|-------|
| 0-4 | Low | 🟢 Green |
| 5-6 | Medium | 🟡 Yellow |
| 7+ | High | 🔴 Red |

## Team File Ownership

| Module | Files |
|--------|-------|
| Core | `cic/core/*` |
| Vision/CV | `cic/vision/*` |
| Video Stream | `cic/api/video.py` |
| Main API | `cic/api.py` |
| Frontend | `frontend/src/*` |

## Merge Notes

- Video code is isolated in `cic/api/video.py` - can be updated without touching main API
- Vision modules are independent - update detector/tracker separately
- Frontend API client supports configurable remote URL via `VITE_API_URL`
