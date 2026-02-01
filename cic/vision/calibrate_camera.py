import cv2
import numpy as np

# --- CONFIGURATION ---
# Camera Resolution
CAM_WIDTH, CAM_HEIGHT = 1920, 1080

# Lists to store the points clicked
calibration_points = []

def mouse_callback(event, x, y, flags, param):
    """
    Function to handle mouse clicks.
    """
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(calibration_points) < 4:
            calibration_points.append((x, y))
            print(f"Point {len(calibration_points)} captured: ({x}, {y})")

def main():
    # Initialize Camera
    cap = cv2.VideoCapture(0)
    
    # Force the resolution to match your hardware
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)

    # Create a window and attach the mouse callback (listener)
    cv2.namedWindow("Calibration: Click 4 Corners")
    cv2.setMouseCallback("Calibration: Click 4 Corners", mouse_callback)

    print("--- CALIBRATION INSTRUCTIONS ---")
    print("1. Click the Top-Left corner of the floor area.")
    print("2. Click the Top-Right corner.")
    print("3. Click the Bottom-Right corner.")
    print("4. Click the Bottom-Left corner.")
    print("5. Press 'q' to finish and generate the code.")
    print("--------------------------------")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Draw circles where user clicked
        for i, pt in enumerate(calibration_points):
            cv2.circle(frame, pt, 5, (0, 0, 255), -1) # Red dot
            cv2.putText(frame, str(i+1), (pt[0]+10, pt[1]-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Draw lines connecting the points to show the box
        if len(calibration_points) > 1:
             cv2.polylines(frame, [np.array(calibration_points)], 
                           isClosed=(len(calibration_points)==4), 
                           color=(0, 255, 255), thickness=2)

        cv2.imshow("Calibration: Click 4 Corners", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # --- PRINT THE RESULT ---
    if len(calibration_points) == 4:
        print("\n\nSUCCESS! COPY AND PASTE THIS INTO YOUR MAIN SCRIPT:\n")
        print("src_points = np.float32([")
        print(f"    [{calibration_points[0][0]}, {calibration_points[0][1]}],  # Top-Left")
        print(f"    [{calibration_points[1][0]}, {calibration_points[1][1]}],  # Top-Right")
        print(f"    [{calibration_points[2][0]}, {calibration_points[2][1]}],  # Bottom-Right")
        print(f"    [{calibration_points[3][0]}, {calibration_points[3][1]}]   # Bottom-Left")
        print("])")
    else:
        print("\nCalibration incomplete. You need to click exactly 4 points.")

if __name__ == "__main__":
    main()