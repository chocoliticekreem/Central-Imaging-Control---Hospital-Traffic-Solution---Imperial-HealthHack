"""
Streamlit Dashboard
===================
OWNER: Dashboard Team (Person E, F)
DEPENDENCIES: streamlit, core modules, pipeline bridge

Main UI for Aegis Flow. Displays:
- Left: Video feed with bounding box overlays
- Right: Priority worklist of patients
- Top: Mode toggle (Live / Demo)
- Demo controls when in demo mode

Run with: streamlit run aegis_flow/interface/dashboard.py

TODO for implementer:
1. Set up Streamlit page config and dark theme
2. Create layout (sidebar, columns)
3. Implement video display with overlays
4. Implement priority worklist cards
5. Implement demo mode controls
6. Connect to StateManager for data
7. Poll bridge for CV updates
"""

import streamlit as st
import time

# Uncomment when core modules are implemented:
# from ..core import StateManager, Patient
# from ..pipeline import PipelineBridge
# from ..core.scoring import format_time_since
import config


def setup_page():
    """
    Configure Streamlit page settings.

    TODO:
    - Set page title: "Aegis Flow - ED Monitor"
    - Set layout to "wide"
    - Set dark theme via config
    """
    st.set_page_config(
        page_title="Aegis Flow - ED Monitor",
        page_icon="🏥",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS for clinical HUD look
    st.markdown("""
    <style>
    /* Dark theme overrides */
    .stApp {
        background-color: #0e1117;
    }

    /* Patient card styles */
    .patient-card {
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    .patient-safe { background-color: #1a3d1a; border-left: 4px solid #28a745; }
    .patient-at-risk { background-color: #3d3d1a; border-left: 4px solid #ffc107; }
    .patient-critical { background-color: #3d1a1a; border-left: 4px solid #dc3545; }

    /* Pulsing animation for critical */
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    .critical-pulse { animation: pulse 1s infinite; }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """
    Render the top header with mode toggle.

    TODO:
    - Display "Aegis Flow" title
    - Add toggle for Live/Demo mode (use st.session_state)
    - Show current FPS from CV pipeline
    """
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.title("Aegis Flow")
        st.caption("Emergency Department Spatial Monitor")

    with col2:
        # TODO: Implement mode toggle
        mode = st.radio("Mode", ["Live", "Demo"], horizontal=True, key="mode")

    with col3:
        # TODO: Show FPS from CV pipeline
        st.metric("FPS", "0.0")


def render_video_panel():
    """
    Render the video feed with bounding box overlays.

    TODO:
    - Get latest frame from bridge
    - Draw bounding boxes for staff (green) and patients (colors by state)
    - Display in st.image()
    - If no frame, show placeholder
    """
    st.subheader("📹 Live Feed")

    # Placeholder for video
    # TODO: Replace with actual video from bridge
    st.info("Video feed will appear here. Connect webcam to enable.")

    # TODO: When implemented:
    # frame = get_latest_frame_from_bridge()
    # if frame is not None:
    #     frame_with_overlays = draw_overlays(frame, state_manager)
    #     st.image(frame_with_overlays, channels="BGR")


def render_patient_card(patient_id: str, state: str, last_interaction: float, priority: float):
    """
    Render a single patient card in the worklist.

    TODO:
    - Display patient ID
    - Show state badge (colored)
    - Show "Last interaction: X min ago"
    - Show priority score
    - Add progress bar showing urgency
    """
    state_colors = {
        "safe": "🟢",
        "at_risk": "🟡",
        "critical": "🔴"
    }

    # TODO: Format time since interaction
    time_ago = f"{int((time.time() - last_interaction) / 60)} min ago"

    css_class = f"patient-{state}"
    if state == "critical":
        css_class += " critical-pulse"

    st.markdown(f"""
    <div class="patient-card {css_class}">
        <strong>{state_colors.get(state, '⚪')} Patient {patient_id}</strong><br>
        <small>Last interaction: {time_ago}</small><br>
        <small>Priority: {priority:.0f}</small>
    </div>
    """, unsafe_allow_html=True)


def render_worklist_panel():
    """
    Render the priority worklist.

    TODO:
    - Get priority list from StateManager
    - Render each patient as a card
    - Sort by priority (highest first)
    - Show empty state if no patients
    """
    st.subheader("📋 Priority Worklist")

    # TODO: Get actual patients from StateManager
    # patients = state_manager.get_priority_list()

    # Placeholder patients for UI development
    st.info("Connect to StateManager to see real patient data.")

    # Example cards (remove when connected):
    # render_patient_card("P001", "critical", time.time() - 1200, 150)
    # render_patient_card("P002", "at_risk", time.time() - 600, 80)
    # render_patient_card("P003", "safe", time.time() - 120, 20)


def render_demo_controls():
    """
    Render demo mode control buttons.

    Only shown when mode == "Demo"

    TODO:
    - "Add Patient" button -> state_manager.demo_add_patient()
    - "Add Staff" button -> state_manager.demo_add_staff()
    - Patient selector dropdown
    - "Trigger Interaction" button
    - "Simulate 5min Neglect" button
    - "Simulate 15min Neglect" button
    - "Clear All" button
    """
    st.subheader("🎮 Demo Controls")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("➕ Add Patient", use_container_width=True):
            # TODO: state_manager.demo_add_patient(...)
            st.success("Patient added!")

        if st.button("➕ Add Staff", use_container_width=True):
            # TODO: state_manager.demo_add_staff(...)
            st.success("Staff added!")

    with col2:
        # TODO: Get patient IDs from StateManager
        patient_id = st.selectbox("Select Patient", ["P001", "P002", "P003"])

        if st.button("🤝 Trigger Interaction", use_container_width=True):
            # TODO: state_manager.demo_trigger_interaction(patient_id)
            st.success(f"Interaction recorded for {patient_id}")

    st.divider()

    st.write("⏩ Fast-forward neglect time:")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("5 min", use_container_width=True):
            # TODO: state_manager.demo_simulate_neglect(patient_id, 5)
            pass

    with col2:
        if st.button("10 min", use_container_width=True):
            # TODO: state_manager.demo_simulate_neglect(patient_id, 10)
            pass

    with col3:
        if st.button("20 min", use_container_width=True):
            # TODO: state_manager.demo_simulate_neglect(patient_id, 20)
            pass

    st.divider()

    if st.button("🗑️ Clear All", type="secondary", use_container_width=True):
        # TODO: state_manager.demo_clear_all()
        st.warning("All entities cleared!")


def run_dashboard():
    """
    Main dashboard entry point.

    TODO:
    1. Initialize StateManager (singleton)
    2. Set up bridge connection to CV process
    3. Render UI components
    4. Poll for updates in a loop (use st.empty() for updates)
    """
    setup_page()
    render_header()

    # Main content layout
    col1, col2 = st.columns([2, 1])

    with col1:
        render_video_panel()

    with col2:
        render_worklist_panel()

        # Show demo controls only in demo mode
        if st.session_state.get("mode") == "Demo":
            st.divider()
            render_demo_controls()

    # Auto-refresh
    # TODO: Replace with proper bridge polling
    time.sleep(config.DASHBOARD_REFRESH_RATE)
    st.rerun()


# Entry point when running directly with streamlit
if __name__ == "__main__":
    run_dashboard()
