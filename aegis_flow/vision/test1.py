import cv2
import numpy as np
from ultralytics import YOLO

# --- CONFIGURATION ---
# Load a pre-trained YOLO model (n for nano is fastest)
model = YOLO('yolov8n.pt') 

# Map dimensions (simulating a hospital floor plan)
MAP_WIDTH, MAP_HEIGHT = 600, 600
map_img = np.zeros((MAP_HEIGHT, MAP_WIDTH, 3), dtype=np.uint8)

# --- CALIBRATION VARIABLES ---
# Adjusted to cover the full width of the bottom half of the screen
# Order: Top-Left, Top-Right, Bottom-Right, Bottom-Left
src_points = np.float32([
    [489, 692],  # Top-Left
    [1101, 657],  # Top-Right
    [1849, 1071],  # Bottom-Right
    [245, 1073]   # Bottom-Left
])

# These map to the 4 corners of our top-down map
dst_points = np.float32([
    [0, 0],                  # Map Top-Left
    [MAP_WIDTH, 0],          # Map Top-Right
    [MAP_WIDTH, MAP_HEIGHT], # Map Bottom-Right
    [0, MAP_HEIGHT]          # Map Bottom-Left
])

# These map to the 4 corners of our top-down map
dst_points = np.float32([
    [0, 0],              # Map Top-Left
    [MAP_WIDTH, 0],      # Map Top-Right
    [MAP_WIDTH, MAP_HEIGHT], # Map Bottom-Right
    [0, MAP_HEIGHT]      # Map Bottom-Left
])

# Calculate the Homography Matrix
matrix = cv2.getPerspectiveTransform(src_points, dst_points)

def get_foot_position(box):
    """
    Calculates the bottom center of the bounding box (the feet).
    """
    x1, y1, x2, y2 = box
    foot_x = int((x1 + x2) / 2)
    foot_y = int(y2)
    return (foot_x, foot_y)

def transform_point(point, matrix):
    """
    Applies the homography matrix to convert camera coords to map coords.
    """
    # Reshape point to be compatible with cv2.perspectiveTransform
    # Shape needs to be (1, 1, 2)
    p = np.array([[[point[0], point[1]]]], dtype=np.float32)
    transformed = cv2.perspectiveTransform(p, matrix)
    
    # Extract coordinates
    tx = int(transformed[0][0][0])
    ty = int(transformed[0][0][1])
    return (tx, ty)

# --- MAIN LOOP ---
cap = cv2.VideoCapture(0) # 0 for default webcam
# print(f"Camera Resolution: {cap.get(3)} x {cap.get(4)}")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Reset map for this frame (clear previous dots)
    # In a real app, you might want to keep trails or use a static map image background
    display_map = map_img.copy()
    cv2.rectangle(display_map, (0,0), (MAP_WIDTH, MAP_HEIGHT), (255, 255, 255), -1) # White background
    
    # 1. Run YOLO Tracking
    # persist=True allows the model to assign unique IDs to people across frames
    results = model.track(frame, persist=True, classes=[0], verbose=False) # class 0 is Person

    # Visualize calibration points on camera feed (for debugging)
    cv2.polylines(frame, [np.int32(src_points)], True, (0, 255, 255), 2)

    if results[0].boxes.id is not None:
        # Get boxes and IDs
        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.int().cpu().numpy()

        for box, track_id in zip(boxes, track_ids):
            # 2. Get Foot Position
            foot_pos = get_foot_position(box)
            
            # 3. Translate to Map Coordinates
            map_pos = transform_point(foot_pos, matrix)
            
            # --- VISUALIZATION ---
            
            # Draw on Camera View
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.circle(frame, foot_pos, 5, (0, 0, 255), -1)
            cv2.putText(frame, f"ID: {track_id}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Draw on Top-Down Map
            # Check if point is inside map bounds before drawing
            if 0 <= map_pos[0] < MAP_WIDTH and 0 <= map_pos[1] < MAP_HEIGHT:
                cv2.circle(display_map, map_pos, 10, (255, 0, 0), -1) # Blue dot for patient
                cv2.putText(display_map, f"ID {track_id}", (map_pos[0]+15, map_pos[1]), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

    # Show the dual display
    cv2.imshow("Hospital CCTV - Patient Tracking", frame)
    cv2.imshow("Top-Down Map Display", display_map)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
