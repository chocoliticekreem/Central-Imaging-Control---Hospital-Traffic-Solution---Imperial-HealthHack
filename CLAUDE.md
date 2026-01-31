# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Aegis Flow** - Patient location system for hospital EDs using CCTV + Re-ID tracking with NEWS2 scoring.

**Key insight:** NHS ELR tells WHO needs help. Aegis Flow tells WHERE they are.

## Tech Stack

- **CV**: YOLOv8, OpenCV, Re-ID (color histogram)
- **UI**: Streamlit
- **Patient Data**: Mock ELR with NEWS2 scoring

## Quick Start

```bash
# Install dependencies
pip install ultralytics opencv-python numpy streamlit Pillow

# Test webcam detection
python aegis_flow/test_webcam.py

# Run dashboard
streamlit run aegis_flow/interface/dashboard.py
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
| 0-4 | Low | 🟢 Green | Routine |
| 5-6 | Medium | 🟡 Yellow | Urgent review |
| 7+ | High | 🔴 Red | Emergency |

## Key Files

| File | Purpose |
|------|---------|
| `vision/detector.py` | YOLO person detection |
| `vision/tracker.py` | Centroid tracking with IDs |
| `vision/classifier.py` | Staff/patient by uniform color |
| `vision/reid.py` | Re-ID signature matching |
| `core/state_manager.py` | Central state + enrollment |
| `core/elr_mock.py` | Mock NHS patient data |
| `interface/dashboard.py` | Streamlit map UI |
| `test_webcam.py` | Webcam test script |

## Team Tasks (4 People)

| Person | Focus | Files |
|--------|-------|-------|
| 1 | Vision Pipeline | `vision/*`, `test_webcam.py` |
| 2 | Dashboard UI | `interface/dashboard.py` |
| 3 | Enrollment + NEWS2 | `interface/dashboard.py`, `core/*` |
| 4 | Integration | `pipeline/*`, connect webcam→UI |
