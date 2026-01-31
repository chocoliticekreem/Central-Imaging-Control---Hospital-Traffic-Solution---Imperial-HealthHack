"""
Aegis Flow Dashboard
====================
Main Streamlit UI with map view, patient list, and controls.

Run: streamlit run aegis_flow/interface/dashboard.py
"""

import streamlit as st
from PIL import Image, ImageDraw
import sys
import os
import random

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aegis_flow.core.state_manager import StateManager
from aegis_flow.core.elr_mock import ELRMock


def init_session():
    """Initialize session state."""
    if "sm" not in st.session_state:
        st.session_state.sm = StateManager()


def render_map(sm) -> Image.Image:
    """Render floor plan with patient dots."""
    img = sm.floor_plan.get_image()
    if not img:
        img = sm.floor_plan.create_demo_floor_plan()

    img = img.copy()
    draw = ImageDraw.Draw(img)

    # Draw identified patients
    for person, record in sm.get_tracked_patients():
        x, y = person.map_position
        color = record.status_color

        # Size based on risk
        r = {"high": 18, "medium": 14, "low": 10}.get(record.risk_level, 10)

        # Draw dot
        draw.ellipse([x-r, y-r, x+r, y+r], fill=color, outline="white", width=2)

        # Draw NEWS2 score
        draw.text((x-6, y-8), str(record.news2_score), fill="white")

        # Draw label
        draw.text((x+r+5, y-8), f"{record.patient_id}", fill="white")

    # Draw unidentified people (gray)
    for person in sm.get_unidentified():
        x, y = person.map_position
        if person.person_type == "staff":
            color = "#0d6efd"  # Blue for staff
        else:
            color = "#6c757d"  # Gray for unknown
        draw.ellipse([x-8, y-8, x+8, y+8], fill=color, outline="white", width=1)
        draw.text((x+12, y-6), person.track_id, fill="#aaa")

    return img


def render_patient_list(sm):
    """Render patient list by risk level."""
    st.subheader("📋 Patients by Risk")

    # High risk
    high = sm.elr.get_patients_by_risk("high")
    if high:
        st.error(f"🔴 HIGH RISK - NEWS2 ≥ 7 ({len(high)})")
        for p in high:
            located = "📍" if sm.is_patient_located(p.patient_id) else "❓"
            st.markdown(f"**{located} {p.patient_id}**: {p.name}")
            st.caption(f"NEWS2: **{p.news2_score}** | {p.chief_complaint} | Wait: {p.wait_time_mins}min")

    # Medium risk
    med = sm.elr.get_patients_by_risk("medium")
    if med:
        st.warning(f"🟡 MEDIUM - NEWS2 5-6 ({len(med)})")
        for p in med:
            located = "📍" if sm.is_patient_located(p.patient_id) else "❓"
            st.markdown(f"**{located} {p.patient_id}**: {p.name}")
            st.caption(f"NEWS2: **{p.news2_score}** | {p.chief_complaint}")

    # Low risk
    low = sm.elr.get_patients_by_risk("low")
    if low:
        st.success(f"🟢 LOW - NEWS2 0-4 ({len(low)})")
        for p in low:
            located = "📍" if sm.is_patient_located(p.patient_id) else "❓"
            st.write(f"{located} **{p.patient_id}**: {p.name} (NEWS2: {p.news2_score})")


def render_enrollment_panel(sm):
    """Render patient enrollment controls."""
    st.subheader("🏷️ Patient Enrollment")

    unidentified = sm.get_unidentified()
    patients_only = [p for p in unidentified if p.person_type != "staff"]

    if not patients_only:
        st.info("No unidentified patients to enroll")
        return

    st.write(f"{len(patients_only)} unidentified patient(s)")

    # Select person
    track_options = {f"{p.track_id} at {p.map_position}": p.track_id for p in patients_only}
    selected = st.selectbox("Select person", list(track_options.keys()))
    track_id = track_options[selected]

    # Select patient from ELR
    all_patients = sm.elr.get_all_patients()
    enrolled = sm.get_enrolled_patient_ids()
    available = [p for p in all_patients if p.patient_id not in enrolled]

    if not available:
        st.warning("All patients already enrolled")
        return

    patient_options = {f"{p.patient_id}: {p.name} (NEWS2: {p.news2_score})": p.patient_id for p in available}
    selected_patient = st.selectbox("Assign to", list(patient_options.keys()))
    patient_id = patient_options[selected_patient]

    if st.button("✓ Enroll Patient", type="primary", use_container_width=True):
        if sm.enroll_patient(track_id, patient_id):
            st.success(f"Enrolled {track_id} as {patient_id}!")
            st.rerun()
        else:
            st.error("Enrollment failed")


def render_vitals_panel(sm):
    """Render vitals update panel."""
    st.subheader("💉 Update Vitals")

    patients = sm.elr.get_all_patients()
    if not patients:
        return

    patient_id = st.selectbox(
        "Patient",
        [p.patient_id for p in patients],
        format_func=lambda x: f"{x}: {sm.elr.get_patient(x).name}"
    )

    patient = sm.elr.get_patient(patient_id)

    # Current NEWS2
    col1, col2 = st.columns(2)
    col1.metric("NEWS2", patient.news2_score)
    col2.metric("Risk", patient.risk_level.upper())

    # Quick actions
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬆️ Deteriorate", use_container_width=True):
            sm.elr.demo_deteriorate(patient_id)
            st.rerun()
    with col2:
        if st.button("⬇️ Improve", use_container_width=True):
            sm.elr.demo_improve(patient_id)
            st.rerun()

    # Detailed vitals (expandable)
    with st.expander("Edit Vitals"):
        resp = st.slider("Respiratory Rate", 8, 35, patient.respiratory_rate)
        spo2 = st.slider("SpO2 %", 80, 100, patient.oxygen_saturation)
        pulse = st.slider("Pulse", 40, 150, patient.pulse)
        bp = st.slider("Systolic BP", 70, 220, patient.systolic_bp)

        if st.button("Update & Recalculate"):
            sm.elr.update_vitals(patient_id,
                respiratory_rate=resp,
                oxygen_saturation=spo2,
                pulse=pulse,
                systolic_bp=bp
            )
            st.rerun()


def render_demo_controls(sm):
    """Render demo mode controls."""
    st.subheader("🎮 Demo Mode")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🎲 Setup Demo", use_container_width=True):
            sm.demo_setup()
            st.rerun()

    with col2:
        if st.button("🗑️ Clear All", use_container_width=True):
            sm.demo_clear_all()
            st.rerun()

    if st.button("➕ Add Random Person", use_container_width=True):
        cam = random.choice(["cam_corridor", "cam_waiting", "cam_triage"])
        pos = (random.randint(100, 700), random.randint(100, 500))
        ptype = random.choice(["patient", "patient", "patient", "staff"])
        sm.demo_add_person(cam, pos, ptype)
        st.rerun()


def render_stats(sm):
    """Render statistics."""
    stats = sm.get_stats()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Tracked", stats["total_tracked"])
    col2.metric("🏷️ Enrolled", stats["tagged_patients"])
    col3.metric("🔴 Critical", stats["critical_located"])
    col4.metric("🟡 Urgent", stats["urgent_located"])


def main():
    # Page config
    st.set_page_config(
        page_title="Aegis Flow",
        page_icon="🏥",
        layout="wide"
    )

    # Initialize
    init_session()
    sm = st.session_state.sm

    # Header
    st.title("🏥 Aegis Flow - Patient Locator")
    st.caption("Real-time patient tracking with NEWS2 monitoring")

    # Stats bar
    render_stats(sm)

    st.divider()

    # Main layout
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📍 Floor Plan")
        map_img = render_map(sm)
        st.image(map_img, use_container_width=True)

        # Legend
        st.caption("🔴 High Risk (NEWS2 ≥7) | 🟡 Medium (5-6) | 🟢 Low (0-4) | 🔵 Staff | ⚫ Unidentified")

    with col2:
        render_patient_list(sm)

    # Sidebar
    with st.sidebar:
        st.title("⚙️ Controls")

        render_enrollment_panel(sm)
        st.divider()

        render_vitals_panel(sm)
        st.divider()

        render_demo_controls(sm)

        st.divider()
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()


if __name__ == "__main__":
    main()
