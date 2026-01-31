import cv2
import numpy as np
from ultralytics import YOLO
import torch
import torchvision.transforms as T
import torchvision.models as models
from scipy.spatial.distance import cosine

# --- SYSTEM SETUP ---
device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
print(f"Running Neural Network on: {device}")

# --- AI MODEL FOR RE-ID (ResNet) ---
feature_extractor = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
feature_extractor = torch.nn.Sequential(*(list(feature_extractor.children())[:-1]))
feature_extractor.to(device)
feature_extractor.eval()

preprocess = T.Compose([
    T.ToPILImage(),
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# --- CONFIGURATION ---
yolo_model = YOLO('yolov8n.pt') 

MAP_WIDTH, MAP_HEIGHT = 600, 600
map_img = np.zeros((MAP_HEIGHT, MAP_WIDTH, 3), dtype=np.uint8)

# --- CALIBRATION (1920x1080) ---
src_points = np.float32([
    [817, 719],  # Top-Left
    [1441, 756],  # Top-Right
    [1664, 1072],  # Bottom-Right
    [216, 1068]   # Bottom-Left
])

# CHANGE: Mirrored the X-coordinates compared to the previous version
# This ensures Left on Camera = Left on Map
dst_points = np.float32([
    [0, MAP_HEIGHT],          # Camera Top-Left  -> Map Bottom-Left
    [MAP_WIDTH, MAP_HEIGHT],  # Camera Top-Right -> Map Bottom-Right
    [MAP_WIDTH, 0],           # Camera Bot-Right -> Map Top-Right
    [0, 0]                    # Camera Bot-Left  -> Map Top-Left
])

matrix = cv2.getPerspectiveTransform(src_points, dst_points)

# --- PATIENT DATABASE ---
patient_db = {}  
next_global_id = 1
MATCH_THRESHOLD = 0.20
# If it thinks two different people are the same person: LOWER the number (e.g., 0.20 or 0.15). This makes the model stricter.
# If it thinks the same person is a new patient: RAISE the number (e.g., 0.30). This makes the model more lenient.


def get_embedding(image_crop):
    img_tensor = preprocess(image_crop).unsqueeze(0).to(device)
    with torch.no_grad():
        features = feature_extractor(img_tensor)
    return features.cpu().numpy().flatten()

def identify_patient(image_crop):
    global next_global_id
    curr_vector = get_embedding(image_crop)
    best_match_id = None
    lowest_dist = 1.0 
    
    for pid, saved_vector in patient_db.items():
        dist = cosine(curr_vector, saved_vector)
        if dist < lowest_dist:
            lowest_dist = dist
            best_match_id = pid
            
    if lowest_dist < MATCH_THRESHOLD:
        return best_match_id, True, curr_vector
    else:
        new_id = next_global_id
        next_global_id += 1
        return new_id, False, curr_vector

active_track_map = {}

# --- MAIN LOOP ---
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

print("Starting Camera... Allow permissions if asked.")

while True:
    ret, frame = cap.read()
    if not ret: break
    
    # 1. Mirror the Camera Feed
    frame = cv2.flip(frame, 1)
    
    display_map = map_img.copy()
    cv2.rectangle(display_map, (0,0), (MAP_WIDTH, MAP_HEIGHT), (255, 255, 255), -1)
    
    # Draw floor zone (visualization)
    cv2.polylines(frame, [np.int32(src_points)], True, (0, 255, 255), 2)

    results = yolo_model.track(frame, persist=True, classes=[0], verbose=False)

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.int().cpu().numpy()

        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = map(int, box)
            
            # Extract Crop
            h, w, _ = frame.shape
            face_crop = frame[max(0,y1):min(h,y2), max(0,x1):min(w,x2)]
            
            if face_crop.size > 0:
                if track_id not in active_track_map:
                    global_id, is_returning, vector = identify_patient(face_crop)
                    active_track_map[track_id] = global_id
                    if is_returning:
                        print(f"ML MATCH: Patient {global_id} returned!")
                    else:
                        patient_db[global_id] = vector
                
                # Adaptive Update
                current_global_id = active_track_map[track_id]
                new_vector = get_embedding(face_crop)
                patient_db[current_global_id] = (0.9 * patient_db[current_global_id]) + (0.1 * new_vector)

            # --- DRAWING ---
            global_display_id = active_track_map.get(track_id, "?")
            
            # Map Logic
            foot_x, foot_y = int((x1 + x2) / 2), int(y2)
            p = np.array([[[foot_x, foot_y]]], dtype=np.float32)
            transformed = cv2.perspectiveTransform(p, matrix)
            map_x, map_y = int(transformed[0][0][0]), int(transformed[0][0][1])

            # Draw on Camera
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"P{global_display_id}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Draw on Map
            if 0 <= map_x < MAP_WIDTH and 0 <= map_y < MAP_HEIGHT:
                cv2.circle(display_map, (map_x, map_y), 15, (255, 0, 0), -1)
                cv2.putText(display_map, f"P{global_display_id}", (map_x+20, map_y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    cv2.imshow("ML Patient Tracking", frame)
    cv2.imshow("Map", display_map)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()