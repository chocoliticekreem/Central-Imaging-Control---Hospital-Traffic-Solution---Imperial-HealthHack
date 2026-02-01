"""
CIC - Main Entry Point
=============================

Starts the full system:
1. CV processing in background process
2. Streamlit dashboard in foreground

Usage:
    python cic/main.py

Or run dashboard directly:
    streamlit run cic/interface/dashboard.py

TODO for implementer:
1. Initialize multiprocessing Queue
2. Start CV processor in background
3. Launch Streamlit dashboard
4. Handle shutdown gracefully (Ctrl+C)
"""

import sys
import os
from multiprocessing import Queue, freeze_support
import subprocess
import signal

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cic.pipeline.processor import run_processor


def main():
    """
    Main entry point.

    TODO:
    1. Create shared Queue for CV-to-UI communication
    2. Start CV processor in separate process
    3. Start Streamlit dashboard
    4. Wait for Ctrl+C, then cleanup
    """
    print("=" * 50)
    print("AEGIS FLOW - Emergency Department Spatial Monitor")
    print("=" * 50)
    print()

    # TODO: Implement full startup sequence
    # For now, just launch the dashboard

    print("Starting dashboard...")
    print("Open http://localhost:8501 in your browser")
    print()
    print("Press Ctrl+C to stop")
    print()

    # Get the path to the dashboard
    dashboard_path = os.path.join(
        os.path.dirname(__file__),
        "interface",
        "dashboard.py"
    )

    # Run streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            dashboard_path,
            "--server.headless", "true"
        ])
    except KeyboardInterrupt:
        print("\nShutting down...")


def main_with_cv():
    """
    Full startup with CV processing.

    TODO (implement this when CV pipeline is ready):
    1. Create Queue
    2. Start CV processor process
    3. Start dashboard with queue reference
    4. Handle cleanup on exit
    """
    from multiprocessing import Process

    print("Starting CIC with CV processing...")

    # Create communication queue
    queue = Queue(maxsize=10)

    # Start CV processor in background
    cv_process = Process(target=run_processor, args=(queue,))
    cv_process.start()
    print(f"CV Processor started (PID: {cv_process.pid})")

    # TODO: Pass queue to dashboard somehow
    # Options:
    # 1. Use a global/singleton
    # 2. Use shared memory
    # 3. Use Redis/other message broker

    # For now, just run dashboard
    main()

    # Cleanup
    print("Stopping CV processor...")
    cv_process.terminate()
    cv_process.join(timeout=5)
    print("Done!")


if __name__ == "__main__":
    freeze_support()  # Required for Windows multiprocessing
    main()
