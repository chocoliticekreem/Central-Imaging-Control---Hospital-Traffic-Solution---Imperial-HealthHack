# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**CIC - Central Imaging Control** - Patient location system for hospital EDs using CCTV + Re-ID tracking with NEWS2 scoring.

**Key insight:** NHS ELR tells WHO needs help. CIC tells WHERE they are.

## Tech Stack

- **Backend**: Python with Flask (cic/vision/app_system2.py)
- **CV**: YOLOv8 + ResNet18 Re-ID + OpenCV
- **Frontend**: HTML templates with MJPEG streaming
- **Deployment**: Local machine with webcam

## Commands

```bash
# Install dependencies
pip install -r cic/requirements.txt

# Run main application (Flask + YOLO + Re-ID)
python cic/vision/app_system2.py

# Run webcam test
python cic/test_webcam.py

# Run Streamlit dashboard (alternative UI)
streamlit run cic/interface/dashboard.py
```

## Architecture

```
Webcam → YOLO → Tracker → Re-ID Match → Map Display
                              ↓
                    ELR (NEWS2 scores) → Color by risk
```

## NEWS2 Risk Levels

| Score | Risk | Color | Action |
|-------|------|-------|--------|
| 0-4 | Low | Green | Routine |
| 5-6 | Medium | Yellow | Urgent review |
| 7+ | High | Red | Emergency |

## Key Files

| File | Purpose |
|------|---------|
| `cic/vision/app_system2.py` | Main Flask app (run this) |
| `cic/vision/templates/index2.html` | Dashboard UI |
| `cic/vision/patients.json` | Mock EPR database |
| `cic/vision/detector.py` | YOLO person detection |
| `cic/vision/tracker.py` | Centroid tracking with IDs |
| `cic/vision/classifier.py` | Staff/patient by uniform color |
| `cic/vision/reid.py` | Re-ID signature matching |
| `cic/core/state_manager.py` | Central state + enrollment |
| `cic/core/elr_mock.py` | Mock NHS patient data |
| `cic/interface/dashboard.py` | Streamlit map UI (alternative) |
| `cic/test_webcam.py` | Webcam test script |
