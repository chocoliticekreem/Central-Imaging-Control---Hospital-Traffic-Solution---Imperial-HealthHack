#!/usr/bin/env python3
"""
Webcam Test Script
==================
Quick test of detection, tracking, classification, and Re-ID.

Run: python aegis_flow/test_webcam.py
Press 'q' to quit, 'e' to enroll current person, 'c' to clear enrollments
"""

import cv2
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aegis_flow.vision.detector import PersonDetector
from aegis_flow.vision.tracker import CentroidTracker
from aegis_flow.vision.classifier import UniformClassifier
from aegis_flow.vision.reid import ReIDExtractor, ReIDMatcher


def main():
    print("=" * 50)
    print("Aegis Flow - Webcam Test")
    print("=" * 50)
    print()
    print("Controls:")
    print("  q - Quit")
    print("  e - Enroll person as patient (assigns next ID)")
    print("  c - Clear all enrollments")
    print()

    # Initialize components
    print("Initializing detector...")
    detector = PersonDetector(confidence=0.5)

    print("Initializing tracker...")
    tracker = CentroidTracker(max_distance=80, max_missed=15)

    print("Initializing classifier...")
    classifier = UniformClassifier()

    print("Initializing Re-ID...")
    reid_extractor = ReIDExtractor()
    reid_matcher = ReIDMatcher(threshold=0.6)

    # Open webcam
    print("Opening webcam...")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print("ERROR: Could not open webcam!")
        return

    print("Webcam opened! Starting detection loop...")
    print()

    patient_counter = 1001
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # 1. Detect people
        detections = detector.detect(frame)

        # 2. Track people
        tracks = tracker.update(detections)

        # 3. Process each tracked person
        for track_id, tracked in tracks.items():
            x1, y1, x2, y2 = tracked.bbox
            cx, cy = tracked.centroid

            # Classify as staff/patient
            person_type = classifier.classify(frame, tracked.bbox)

            # Extract Re-ID signature
            signature = reid_extractor.extract_signature(frame, tracked.bbox)

            # Try to match against enrolled patients
            match = reid_matcher.match(signature)

            # Determine display info
            if match:
                label = f"{match.patient_id} ({match.confidence:.0%})"
                color = (0, 255, 0)  # Green for identified
            elif person_type == "staff":
                label = f"{track_id} [STAFF]"
                color = (255, 165, 0)  # Orange for staff
            else:
                label = f"{track_id} [?]"
                color = (128, 128, 128)  # Gray for unidentified

            # Draw bounding box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Draw label background
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame, (x1, y1 - 25), (x1 + label_size[0] + 10, y1), color, -1)

            # Draw label text
            cv2.putText(frame, label, (x1 + 5, y1 - 7),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            # Draw center point
            cv2.circle(frame, (cx, cy), 5, color, -1)

        # Draw info overlay
        info_lines = [
            f"Detected: {len(detections)} | Tracked: {len(tracks)}",
            f"Enrolled: {len(reid_matcher.get_enrolled_ids())} patients",
            f"Frame: {frame_count}",
            "",
            "Press 'e' to enroll | 'c' to clear | 'q' to quit"
        ]

        for i, line in enumerate(info_lines):
            cv2.putText(frame, line, (10, 30 + i * 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Show frame
        cv2.imshow("Aegis Flow - Webcam Test", frame)

        # Handle key presses
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        elif key == ord('e'):
            # Enroll first unidentified person
            for track_id, tracked in tracks.items():
                person_type = classifier.classify(frame, tracked.bbox)
                if person_type == "patient":
                    signature = reid_extractor.extract_signature(frame, tracked.bbox)
                    match = reid_matcher.match(signature)
                    if not match:
                        patient_id = f"P-{patient_counter}"
                        reid_matcher.enroll(patient_id, signature)
                        print(f"Enrolled {track_id} as {patient_id}")
                        patient_counter += 1
                        break

        elif key == ord('c'):
            # Clear enrollments
            for pid in list(reid_matcher.get_enrolled_ids()):
                reid_matcher.unenroll(pid)
            print("Cleared all enrollments")

    cap.release()
    cv2.destroyAllWindows()
    print("Done!")


if __name__ == "__main__":
    main()
