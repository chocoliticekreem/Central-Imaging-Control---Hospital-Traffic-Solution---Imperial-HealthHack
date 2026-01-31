# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Aegis Flow** - A spatial intelligence platform for hospital emergency departments. Uses computer vision to track patients and staff, calculate "neglect time" (time since last staff interaction), and present a priority-ranked worklist.

## Tech Stack

- **Backend**: Python 3.10+
- **CV Pipeline**: YOLOv8 (ultralytics), OpenCV
- **UI**: Streamlit
- **IPC**: multiprocessing.Queue (CV process → UI process)

## Commands

```bash
# Install dependencies
pip install -r aegis_flow/requirements.txt

# Run dashboard only (for UI development)
streamlit run aegis_flow/interface/dashboard.py

# Run full system (CV + dashboard)
python aegis_flow/main.py
```

## Architecture

```
CV Process (heavy)          UI Process (light)
┌─────────────────┐         ┌─────────────────┐
│ Webcam Capture  │         │                 │
│       ↓         │         │  StateManager   │←── Demo Buttons
│ YOLO Detection  │         │  (Central Hub)  │
│       ↓         │  Queue  │       ↓         │
│ Centroid Track  │────────▶│ Priority List   │
│       ↓         │         │       ↓         │
│ Color Classify  │         │  Streamlit UI   │
│       ↓         │         │                 │
│ Interaction Det │         └─────────────────┘
└─────────────────┘
```

## Module Ownership

| Module | Path | Purpose |
|--------|------|---------|
| Core | `aegis_flow/core/` | Entities, StateManager, scoring |
| Vision | `aegis_flow/vision/` | Detection, tracking, classification |
| Pipeline | `aegis_flow/pipeline/` | CV↔UI bridge, processor loop |
| Interface | `aegis_flow/interface/` | Streamlit dashboard |

## Key Files

- `config.py` - All tunable parameters (thresholds, colors, etc.)
- `core/state_manager.py` - Central state hub, all updates flow through here
- `vision/detector.py` - YOLO wrapper for person detection
- `interface/dashboard.py` - Main Streamlit UI

## State Transitions

Patient states based on `time_since_last_interaction`:
- **safe** (green): < 5 min
- **at_risk** (yellow): 5-15 min
- **critical** (red): > 15 min

## Demo Mode

Demo buttons inject events directly into StateManager, bypassing CV pipeline. Useful for reliable hackathon presentations.
