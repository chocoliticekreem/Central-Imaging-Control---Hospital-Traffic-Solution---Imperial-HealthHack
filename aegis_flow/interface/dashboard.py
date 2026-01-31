"""
Aegis Flow Dashboard
====================
Main Streamlit UI with live webcam feed and map view.

Run: streamlit run aegis_flow/interface/dashboard.py
"""

import streamlit as st
from PIL import Image, ImageDraw
import sys
import os
import random
import time
import cv2
import numpy as np

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
root_dir = os.path.dirname(parent_dir)
sys.path.insert(0, root_dir)
sys.path.insert(0, parent_dir)

try:
    from aegis_flow.core.state_manager import StateManager
    from aegis_flow.vision.detector import PersonDetector
    from aegis_flow.vision.tracker import CentroidTracker
    from aegis_flow.vision.classifier import UniformClassifier
    from aegis_flow.vision.reid import ReIDExtractor, ReIDMatcher
except ImportError:
    from core.state_manager import StateManager
    from vision.detector import PersonDetector
    from vision.tracker import CentroidTracker
    from vision.classifier import UniformClassifier
    from vision.reid import ReIDExtractor, ReIDMatcher


@st.cache_resource
def get_detector():
    """Cache the YOLO detector."""
    return PersonDetector(confidence=0.5)


@st.cache_resource
def get_tracker():
    """Cache the tracker."""
    return CentroidTracker(max_distance=80, max_missed=15)


@st.cache_resource
def get_classifier():
    """Cache the classifier."""
    return UniformClassifier()


@st.cache_resource
def get_reid():
    """Cache Re-ID components."""
    return ReIDExtractor(), ReIDMatcher(threshold=0.6)


def init_session():
    """Initialize session state."""
    if "sm" not in st.session_state:
        st.session_state.sm = StateManager()
        # Auto-setup demo data
        st.session_state.sm.floor_plan.setup_demo_zones()
        st.session_state.sm.floor_plan.create_demo_floor_plan()

    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = False

    if "webcam_active" not in st.session_state:
        st.session_state.webcam_active = False

    if "camera" not in st.session_state:
        st.session_state.camera = None


def process_frame(frame, detector, tracker, classifier, reid_extractor, reid_matcher, sm):
    """Process a single frame through the CV pipeline."""
    # Detect people
    detections = detector.detect(frame)

    # Track people
    tracks = tracker.update(detections)

    # Process each tracked person
    for track_id, tracked in tracks.items():
        # Classify as staff/patient
        person_type = classifier.classify(frame, tracked.bbox)

        # Extract Re-ID signature
        signature = reid_extractor.extract_signature(frame, tracked.bbox)

        # Try to match against enrolled patients
        match = reid_matcher.match(signature)

        # Update state manager
        person = sm.update_tracked(
            track_id=track_id,
            camera_id="cam_webcam",
            position=tracked.centroid,
            person_type=person_type
        )

        # If matched, link to patient
        if match and not person.patient_id:
            sm.tag_patient(track_id, match.patient_id)

    return tracks


def draw_detections(frame, tracks, classifier, reid_matcher, sm):
    """Draw bounding boxes and labels on frame."""
    frame = frame.copy()

    for track_id, tracked in tracks.items():
        x1, y1, x2, y2 = tracked.bbox
        cx, cy = tracked.centroid

        # Get person info
        person_type = classifier.classify(frame, tracked.bbox)

        # Check if enrolled
        person = None
        for p in sm.get_all_tracked():
            if p.track_id == track_id:
                person = p
                break

        # Determine color and label
        if person and person.patient_id:
            record = sm.elr.get_patient(person.patient_id)
            if record:
                color_map = {"high": (0, 0, 255), "medium": (0, 255, 255), "low": (0, 255, 0)}
                color = color_map.get(record.risk_level, (128, 128, 128))
                label = f"{record.patient_id} NEWS2:{record.news2_score}"
            else:
                color = (128, 128, 128)
                label = track_id
        elif person_type == "staff":
            color = (255, 165, 0)  # Orange
            label = f"{track_id} [STAFF]"
        else:
            color = (128, 128, 128)  # Gray
            label = f"{track_id} [?]"

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        # Draw label background
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.rectangle(frame, (x1, y1 - 25), (x1 + label_size[0] + 10, y1), color, -1)

        # Draw label
        cv2.putText(frame, label, (x1 + 5, y1 - 7),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Draw center point
        cv2.circle(frame, (cx, cy), 5, color, -1)

    return frame


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

        # Outer glow for critical
        if record.risk_level == "high":
            draw.ellipse([x-28, y-28, x+28, y+28], fill=None, outline="#ff4444", width=3)
            r = 18
        elif record.risk_level == "medium":
            draw.ellipse([x-20, y-20, x+20, y+20], fill=None, outline="#ffcc00", width=2)
            r = 14
        else:
            r = 10

        draw.ellipse([x-r, y-r, x+r, y+r], fill=color, outline="white", width=2)
        draw.text((x-4, y-7), str(record.news2_score), fill="white")
        draw.text((x+r+5, y-8), record.patient_id, fill="white")

    # Draw unidentified
    for person in sm.get_unidentified():
        x, y = person.map_position
        color = "#0d6efd" if person.person_type == "staff" else "#6c757d"
        draw.ellipse([x-8, y-8, x+8, y+8], fill=color, outline="white", width=1)
        draw.text((x+12, y-6), person.track_id, fill="#aaa")

    return img


def render_critical_alerts(sm):
    """Show alert banner for critical patients."""
    critical = [(p, r) for p, r in sm.get_tracked_patients() if r.risk_level == "high"]

    if not critical:
        return

    st.error(f"🚨 **{len(critical)} CRITICAL PATIENT(S)** - Immediate attention required!")

    cols = st.columns(min(len(critical), 3))
    for i, (person, record) in enumerate(critical):
        with cols[i % 3]:
            zone = sm.get_zone_name(person.map_position)
            st.markdown(f"""
            **{record.patient_id}**: {record.name}
            📍 {zone} | NEWS2: **{record.news2_score}**
            _{record.chief_complaint}_
            """)


def render_patient_list(sm):
    """Render patient list."""
    st.subheader("📋 Patients")

    for risk, icon, expanded in [("high", "🔴", True), ("medium", "🟡", True), ("low", "🟢", False)]:
        patients = sm.elr.get_patients_by_risk(risk)
        if patients:
            with st.expander(f"{icon} {risk.upper()} ({len(patients)})", expanded=expanded):
                for p in patients:
                    located = "📍" if sm.is_patient_located(p.patient_id) else "❓"
                    st.write(f"{located} **{p.patient_id}**: {p.name} (NEWS2: {p.news2_score})")


def render_enrollment_panel(sm, reid_matcher):
    """Render enrollment controls."""
    st.subheader("🏷️ Enrollment")

    unidentified = [p for p in sm.get_unidentified() if p.person_type != "staff"]

    if not unidentified:
        st.success("✓ All enrolled")
        return

    st.warning(f"{len(unidentified)} unidentified")

    track_id = st.selectbox("Person", [p.track_id for p in unidentified])

    enrolled = sm.get_enrolled_patient_ids()
    available = [p for p in sm.elr.get_all_patients() if p.patient_id not in enrolled]

    if available:
        patient_id = st.selectbox("Patient", [p.patient_id for p in available],
                                  format_func=lambda x: f"{x}: {sm.elr.get_patient(x).name}")

        if st.button("✓ Enroll", type="primary", use_container_width=True):
            sm.enroll_patient(track_id, patient_id)
            st.success("Enrolled!")
            st.rerun()


def render_vitals_panel(sm):
    """Render vitals panel."""
    st.subheader("💉 Vitals")

    patients = sm.elr.get_all_patients()
    patient_id = st.selectbox("Patient", [p.patient_id for p in patients],
                              format_func=lambda x: f"{x}: {sm.elr.get_patient(x).name}",
                              key="vitals_select")

    patient = sm.elr.get_patient(patient_id)

    # Big NEWS2 display
    colors = {"high": "#dc3545", "medium": "#ffc107", "low": "#28a745"}
    st.markdown(f"<h1 style='text-align:center; color:{colors[patient.risk_level]}'>{patient.news2_score}</h1>",
                unsafe_allow_html=True)
    st.caption(f"NEWS2 Score - {patient.risk_level.upper()} risk")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬆️ Worse", use_container_width=True):
            sm.elr.demo_deteriorate(patient_id)
            st.rerun()
    with col2:
        if st.button("⬇️ Better", use_container_width=True):
            sm.elr.demo_improve(patient_id)
            st.rerun()


def render_demo_controls(sm):
    """Render demo controls."""
    st.subheader("🎮 Demo")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎲 Add Demo Data", use_container_width=True):
            sm.demo_setup()
            st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            sm.demo_clear_all()
            st.rerun()

    if st.button("➕ Add Person", use_container_width=True):
        cam = random.choice(["cam_corridor", "cam_waiting", "cam_triage"])
        pos = (random.randint(80, 720), random.randint(120, 480))
        sm.demo_add_person(cam, pos, "patient")
        st.rerun()


def main():
    st.set_page_config(page_title="Aegis Flow", page_icon="🏥", layout="wide")

    # Initialize
    init_session()
    sm = st.session_state.sm

    # Get CV components
    detector = get_detector()
    tracker = get_tracker()
    classifier = get_classifier()
    reid_extractor, reid_matcher = get_reid()

    # Header
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.title("🏥 Aegis Flow")
    with col2:
        webcam_on = st.checkbox("📷 Webcam", value=st.session_state.webcam_active)
        st.session_state.webcam_active = webcam_on
    with col3:
        auto_refresh = st.checkbox("🔄 Auto", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh

    # Stats
    stats = sm.get_stats()
    cols = st.columns(5)
    cols[0].metric("👥 Tracked", stats["total_tracked"])
    cols[1].metric("🏷️ Enrolled", stats["tagged_patients"])
    cols[2].metric("❓ Unknown", stats["untagged"])
    cols[3].metric("🔴 Critical", stats["critical_located"])
    cols[4].metric("🟡 Urgent", stats["urgent_located"])

    # Critical alerts
    render_critical_alerts(sm)

    st.divider()

    # Main content
    if webcam_on:
        # Webcam mode: show camera + map side by side
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📷 Live Feed")
            video_placeholder = st.empty()

            # Open camera
            cap = cv2.VideoCapture(0)

            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    # Process frame
                    tracks = process_frame(frame, detector, tracker, classifier,
                                          reid_extractor, reid_matcher, sm)

                    # Draw detections
                    frame_with_boxes = draw_detections(frame, tracks, classifier, reid_matcher, sm)

                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame_with_boxes, cv2.COLOR_BGR2RGB)

                    # Display
                    video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

                cap.release()
            else:
                st.error("Could not open webcam")

        with col2:
            st.subheader("📍 Map")
            map_img = render_map(sm)
            st.image(map_img, use_container_width=True)
    else:
        # Map-only mode
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📍 Floor Plan")
            map_img = render_map(sm)
            st.image(map_img, use_container_width=True)
            st.caption("🔴 High | 🟡 Medium | 🟢 Low | 🔵 Staff | ⚫ Unknown")

        with col2:
            render_patient_list(sm)

    # Sidebar
    with st.sidebar:
        st.title("⚙️ Controls")

        render_enrollment_panel(sm, reid_matcher)
        st.divider()

        render_vitals_panel(sm)
        st.divider()

        render_demo_controls(sm)

    # Auto-refresh
    if auto_refresh or webcam_on:
        time.sleep(0.5 if webcam_on else 2)
        st.rerun()


if __name__ == "__main__":
    main()
