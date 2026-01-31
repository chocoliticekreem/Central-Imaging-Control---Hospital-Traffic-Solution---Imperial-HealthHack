# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Aegis Flow** - A patient location system for hospital emergency departments. Uses CCTV/webcam to track people and show their locations on a floor plan map. Nurses can see WHERE critical patients are, not just WHO they are.

**Key insight:** NHS ELR tells nurses WHO needs help. Aegis Flow tells them WHERE to go.

## Tech Stack

- **Backend**: Python 3.10+
- **CV Pipeline**: YOLOv8 (ultralytics), OpenCV
- **UI**: Streamlit with floor plan map
- **Patient Data**: Mock ELR feed (JSON)

## Commands

```bash
# Install dependencies
pip install -r aegis_flow/requirements.txt

# Run dashboard (UI development)
streamlit run aegis_flow/interface/dashboard.py

# Run full system
python aegis_flow/main.py
```

## Architecture

```
Camera → Detect → Track → Show on Map
                              ↓
         Nurse clicks dot → Assigns Patient ID (from ELR)
                              ↓
         ELR Feed (JSON) → Colors dot by status
```

## Core Concepts

1. **TrackedPerson**: Someone detected by camera (has track_id, position)
2. **PatientRecord**: Patient info from ELR (has patient_id, status, name)
3. **Tagging**: Nurse links TrackedPerson → PatientRecord by clicking on map
4. **CameraZone**: Maps camera pixels to floor plan coordinates

## Status Colors

- Red: Critical
- Orange: Urgent
- Yellow: Standard
- Green: Stable

## Key Files

| File | Purpose |
|------|---------|
| `core/state_manager.py` | Central hub - tracking + tagging |
| `core/elr_mock.py` | Mock NHS patient feed |
| `core/floor_plan.py` | Map image + camera zones |
| `vision/detector.py` | YOLO person detection |
| `vision/tracker.py` | Persistent ID tracking |
| `vision/classifier.py` | Staff vs patient by uniform |
| `interface/dashboard.py` | Streamlit map UI |
