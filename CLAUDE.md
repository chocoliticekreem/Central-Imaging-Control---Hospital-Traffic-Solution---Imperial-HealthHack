# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Aegis Flow** - Patient location system for hospital EDs using CCTV + Re-ID tracking with NEWS2 scoring.

**Key insight:** NHS ELR tells WHO needs help. Aegis Flow tells WHERE they are.

## Tech Stack

- **CV**: YOLOv8, OpenCV, Re-ID (color histogram)
- **UI**: **Streamlit** — recommended for demo (webcam, map, ELR, enrollment all in one)
- **Optional**: React frontend (`frontend/`) + FastAPI (`aegis_flow/api.py`) for a separate web UI
- **Patient Data**: Mock ELR with NEWS2 scoring

## Quick Start (recommended: Streamlit)

```bash
pip install -r aegis_flow/requirements.txt
streamlit run aegis_flow/interface/dashboard.py
```

One command, one tab: webcam, floor map, patient list, enrollment, vitals. Use this for demos.

Optional: `python aegis_flow/test_webcam.py` for webcam-only test. For React + API: run `uvicorn aegis_flow.api:app --reload --port 8000` then `cd frontend && npm run dev` and open http://localhost:5173.

## Architecture

```
Webcam → YOLO → Tracker → Re-ID Match → Map Display
                              ↓
                    ELR (NEWS2 scores) → Color by risk
```

## NEWS2 Risk Levels

| Score | Risk | Color | Action |
|-------|------|-------|--------|
| 0-4 | Low | 🟢 Green | Routine |
| 5-6 | Medium | 🟡 Yellow | Urgent review |
| 7+ | High | 🔴 Red | Emergency |

## Key Files

| File | Purpose |
|------|---------|
| `interface/dashboard.py` | **Streamlit UI** — webcam, map, ELR, enrollment (use for demo) |
| `vision/detector.py` | YOLO person detection |
| `vision/tracker.py` | Centroid tracking with IDs |
| `vision/classifier.py` | Staff/patient by uniform color |
| `vision/reid.py` | Re-ID signature matching |
| `core/state_manager.py` | Central state + enrollment |
| `core/elr_mock.py` | Mock NHS patient data |
| `test_webcam.py` | Webcam test script |
| `aegis_flow/api.py` | FastAPI backend (for optional React frontend) |
| `frontend/` | Optional React app |

## Team Tasks (4 People)

| Person | Focus | Files |
|--------|-------|-------|
| 1 | Vision Pipeline | `vision/*`, `test_webcam.py` |
| 2 | Dashboard UI | `interface/dashboard.py` (Streamlit) |
| 3 | Enrollment + NEWS2 | `interface/dashboard.py`, `core/*` |
| 4 | Integration | `pipeline/*`, webcam → Streamlit |
