import cv2
import numpy as np
from ultralytics import YOLO

# --- CONFIGURATION ---
# Load the model
model = YOLO('yolov8n.pt') 

# Map dimensions (The size of the white window)
MAP_WIDTH, MAP_HEIGHT = 600, 600
map_img = np.zeros((MAP_HEIGHT, MAP_WIDTH, 3), dtype=np.uint8)

# --- CALIBRATION (SCALED FOR 1920x1080) ---
# I have scaled the previous "skirting board" coordinates 
# to fit your 1920x1080 resolution.
src_points = np.float32([
    [613, 757],  # Top-Left
    [1220, 732],  # Top-Right
    [1839, 1072],  # Bottom-Right
    [408, 1071]   # Bottom-Left
])

dst_points = np.float32([
    [0, 0],                  
    [MAP_WIDTH, 0],          
    [MAP_WIDTH, MAP_HEIGHT], 
    [0, MAP_HEIGHT]          
])

matrix = cv2.getPerspectiveTransform(src_points, dst_points)

# --- PATIENT RE-IDENTIFICATION SYSTEM ---
# Stores { global_id : (shirt_hist, pants_hist) }
patient_db = {}  
next_global_id = 1

# Similarity Threshold (0.0 to 1.0)
# Lower = Easier to match (less strict)
# Higher = Harder to match (more strict)
# 0.5 is a good balance for the "Split Body" method
MATCH_THRESHOLD = 0.5 

def get_patient_fingerprint(image_crop):
    """
    UPGRADE 1: Splits the person into Shirt (Top) and Pants (Bottom).
    This prevents 'Red Shirt' matching with 'Red Pants'.
    """
    (h, w) = image_crop.shape[:2]
    
    # 1. Center Crop: Remove 15% form side edges to cut out background wall noise
    margin_w = int(w * 0.15)
    # Ensure crop isn't too small
    if margin_w > 0 and w - 2*margin_w > 0:
        crop = image_crop[:, margin_w : w - margin_w]
    else:
        crop = image_crop
        
    (h_c, w_c) = crop.shape[:2]
    
    # 2. Split: Top half (Shirt) vs Bottom half (Pants)
    # Using integer division //
    shirt_zone = crop[0 : h_c // 2, :]
    pants_zone = crop[h_c // 2 : h_c, :]
    
    def calc_hist(img_chunk):
        if img_chunk.size == 0: return None
        hsv = cv2.cvtColor(img_chunk, cv2.COLOR_BGR2HSV)
        # 30 Hue bins, 32 Saturation bins. Ignore Value (brightness)
        hist = cv2.calcHist([hsv], [0, 1], None, [30, 32], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 1, cv2.NORM_MINMAX)
        return hist

    return (calc_hist(shirt_zone), calc_hist(pants_zone))

def identify_patient(image_crop):
    """
    Compares the current person against the database of known patients.
    """
    global next_global_id
    
    # Extract current fingerprint
    curr_shirt, curr_pants = get_patient_fingerprint(image_crop)
    if curr_shirt is None or curr_pants is None: return None, False

    best_match_id = None
    highest_score = 0
    
    for pid, (saved_shirt, saved_pants) in patient_db.items():
        # Compare Shirts
        score_shirt = cv2.compareHist(curr_shirt, saved_shirt, cv2.HISTCMP_CORREL)
        # Compare Pants
        score_pants = cv2.compareHist(curr_pants, saved_pants, cv2.HISTCMP_CORREL)
        
        # Weighted Score: We trust the Shirt (70%) more than Pants (30%)
        # because pants are often dark/generic (jeans, black trousers)
        total_score = (score_shirt * 0.7) + (score_pants * 0.3)
        
        if total_score > highest_score:
            highest_score = total_score
            best_match_id = pid
            
    # DEBUG: Uncomment this to see the scores in your terminal!
    # print(f"Best match: P{best_match_id} | Score: {highest_score:.2f}")

    if highest_score > MATCH_THRESHOLD:
        return best_match_id, True  # Returning Patient
    else:
        # Create New Patient
        new_id = next_global_id
        patient_db[new_id] = (curr_shirt, curr_pants)
        next_global_id += 1
        return new_id, False # New Patient

# Dictionary to map current frame YOLO IDs to our Global Patient IDs
# { yolo_track_id : global_patient_id }
active_track_map = {}

# --- MAIN LOOP ---
cap = cv2.VideoCapture(0)

# Force resolution to 1080p to match our calibration
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

while True:
    ret, frame = cap.read()
    if not ret: break
    
    # Prepare the blank map
    display_map = map_img.copy()
    cv2.rectangle(display_map, (0,0), (MAP_WIDTH, MAP_HEIGHT), (255, 255, 255), -1)
    
    # Visual Guide: Draw the yellow "Floor Zone" on the camera
    cv2.polylines(frame, [np.int32(src_points)], True, (0, 255, 255), 2)

    # 1. Run YOLO Tracking
    results = model.track(frame, persist=True, classes=[0], verbose=False)

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.int().cpu().numpy()

        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = map(int, box)
            
            # --- IDENTITY CHECK ---
            # Extract crop of the person
            h_img, w_img, _ = frame.shape
            # Ensure we don't crash by cropping outside the image
            face_crop = frame[max(0,y1):min(h_img,y2), max(0,x1):min(w_img,x2)]
            
            if face_crop.size > 0:
                # If YOLO lost track of this ID (or it's a new ID), check the database
                if track_id not in active_track_map:
                    global_id, is_returning = identify_patient(face_crop)
                    if global_id is not None:
                        active_track_map[track_id] = global_id
                        if is_returning:
                            print(f"DEBUG: Patient {global_id} returned (ID restoration)")
                
                # UPGRADE 2: ADAPTIVE UPDATE
                # Even if we know who they are, we update their photo in the database
                # This ensures that as they walk into shadows, we remember their "darker" version
                current_global_id = active_track_map.get(track_id)
                if current_global_id:
                    curr_shirt, curr_pants = get_patient_fingerprint(face_crop)
                    if curr_shirt is not None:
                         patient_db[current_global_id] = (curr_shirt, curr_pants)

            # --- MAPPING ---
            global_display_id = active_track_map.get(track_id, "?")
            
            # 1. Calc Feet Position
            foot_x = int((x1 + x2) / 2)
            foot_y = int(y2)
            
            # 2. Transform to Map
            p = np.array([[[foot_x, foot_y]]], dtype=np.float32)
            transformed = cv2.perspectiveTransform(p, matrix)
            map_x, map_y = int(transformed[0][0][0]), int(transformed[0][0][1])

            # 3. Draw on Camera
            color = (0, 255, 0) # Green box
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, f"P{global_display_id}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            # 4. Draw on Map
            if 0 <= map_x < MAP_WIDTH and 0 <= map_y < MAP_HEIGHT:
                # Draw dot
                cv2.circle(display_map, (map_x, map_y), 15, (255, 0, 0), -1)
                # Draw Text
                cv2.putText(display_map, f"P{global_display_id}", (map_x+20, map_y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    cv2.imshow("Hospital CCTV - Patient Tracking", frame)
    cv2.imshow("Top-Down Map Display", display_map)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()