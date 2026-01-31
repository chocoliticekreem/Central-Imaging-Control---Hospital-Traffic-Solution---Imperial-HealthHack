"""
Priority Scoring
================
Calculates priority scores for patients to determine worklist order.
Higher score = more urgent = appears higher in the list.
"""

import time
from .entities import Patient

# Weight added to score based on current state
STATE_WEIGHTS = {
    "safe": 0,
    "at_risk": 50,
    "critical": 100
}


def calculate_priority(patient: Patient) -> float:
    """
    Calculate priority score for a patient.
    Higher score = more urgent.

    Formula: time_unattended (seconds) + state_weight
    """
    time_unattended = patient.time_since_interaction()
    state_weight = STATE_WEIGHTS.get(patient.state, 0)
    return time_unattended + state_weight


def format_time_since(timestamp: float) -> str:
    """Format a timestamp as human-readable 'X ago' string."""
    seconds = time.time() - timestamp

    if seconds < 60:
        return f"{int(seconds)} sec ago"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} min ago"
    else:
        hours = int(seconds / 3600)
        return f"{hours} hr ago"


def format_duration(seconds: float) -> str:
    """Format a duration in seconds as human-readable string."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"
