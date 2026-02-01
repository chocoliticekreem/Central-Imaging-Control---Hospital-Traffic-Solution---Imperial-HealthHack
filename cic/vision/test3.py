import cv2
import numpy as np
from ultralytics import YOLO
import torch
import torchvision.transforms as T
import torchvision.models as models
from scipy.spatial.distance import cosine

# --- SYSTEM SETUP ---
# Detect if we are on Mac Apple Silicon (MPS) or standard CPU
device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
print(f"Running Neural Network on: {device}")

# --- AI MODEL FOR RE-ID (ResNet) ---
# We use a standard ResNet18 pre-trained on ImageNet.
# It converts an image of a person into a vector of numbers.
feature_extractor = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
# Remove the final classification layer (we only want the features)
feature_extractor = torch.nn.Sequential(*(list(feature_extractor.children())[:-1]))
feature_extractor.to(device)
feature_extractor.eval() # Set to evaluation mode (no training)

# Standard image preprocessing required by ResNet
preprocess = T.Compose([
    T.ToPILImage(),
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# --- CONFIGURATION ---
yolo_model = YOLO('yolov8n.pt') 

# Map dimensions
MAP_WIDTH, MAP_HEIGHT = 600, 600
map_img = np.zeros((MAP_HEIGHT, MAP_WIDTH, 3), dtype=np.uint8)

# --- CALIBRATION (1920x1080) ---
src_points = np.float32([
    [613, 757],  # Top-Left
    [1220, 732],  # Top-Right
    [1839, 1072],  # Bottom-Right
    [408, 1071]   # Bottom-Left
])

dst_points = np.float32([
    [0, 0], [MAP_WIDTH, 0], [MAP_WIDTH, MAP_HEIGHT], [0, MAP_HEIGHT]
])
matrix = cv2.getPerspectiveTransform(src_points, dst_points)

# --- PATIENT DATABASE ---
# Stores { global_id : feature_vector (numpy array) }
patient_db = {}  
next_global_id = 1

# Similarity Threshold (Cosine Distance)
# Lower distance = More similar. 
# 0.0 is identical. 0.2 is very similar. 0.4 is different.
# Start with 0.25. If it confuses people, lower it to 0.15.
MATCH_THRESHOLD = 0.20
# If it thinks two different people are the same person: LOWER the number (e.g., 0.20 or 0.15). This makes the model stricter.
# If it thinks the same person is a new patient: RAISE the number (e.g., 0.30). This makes the model more lenient.

def get_embedding(image_crop):
    """
    Feeds the image crop into the Neural Network to get a 512-dim vector.
    """
    # 1. Preprocess (Resize, Normalize)
    img_tensor = preprocess(image_crop).unsqueeze(0).to(device)
    
    # 2. Run Inference
    with torch.no_grad():
        features = feature_extractor(img_tensor)
    
    # 3. Flatten to a simple list of numbers
    return features.cpu().numpy().flatten()

def identify_patient(image_crop):
    """
    Compares the current person's vector against the database using Cosine Similarity.
    """
    global next_global_id
    
    # Get current vector
    curr_vector = get_embedding(image_crop)
    
    best_match_id = None
    lowest_dist = 1.0 # 1.0 means completely different
    
    for pid, saved_vector in patient_db.items():
        # Calculate Cosine Distance
        dist = cosine(curr_vector, saved_vector)
        
        if dist < lowest_dist:
            lowest_dist = dist
            best_match_id = pid
            
    # DEBUG: See the math in real-time
    # print(f"Best Match: P{best_match_id} | Distance: {lowest_dist:.4f}")

    if lowest_dist < MATCH_THRESHOLD:
        return best_match_id, True, curr_vector
    else:
        # Create New Patient
        new_id = next_global_id
        next_global_id += 1
        return new_id, False, curr_vector

# Active tracks mapping { yolo_id : global_id }
active_track_map = {}

# --- MAIN LOOP ---
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

print("Starting Camera... Allow permissions if asked.")

while True:
    ret, frame = cap.read()
    if not ret: break
    
    display_map = map_img.copy()
    cv2.rectangle(display_map, (0,0), (MAP_WIDTH, MAP_HEIGHT), (255, 255, 255), -1)
    
    # Draw the yellow floor zone so you know where to stand
    cv2.polylines(frame, [np.int32(src_points)], True, (0, 255, 255), 2)

    # Run YOLO
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
                # Identification Logic
                if track_id not in active_track_map:
                    # NEW PERSON (to YOLO) -> Check Database
                    global_id, is_returning, vector = identify_patient(face_crop)
                    active_track_map[track_id] = global_id
                    
                    if is_returning:
                        print(f"ML MATCH: Patient {global_id} returned!")
                    else:
                        # New patient, save their vector
                        patient_db[global_id] = vector
                
                # ADAPTIVE UPDATE (Upgrade 2 logic applied to ML)
                # If the person is clearly visible, update their vector slightly
                # so the model adapts to lighting changes.
                current_global_id = active_track_map[track_id]
                # We blend the new vector with the old one (Running Average)
                # This keeps the ID stable but adaptable.
                new_vector = get_embedding(face_crop)
                patient_db[current_global_id] = (0.9 * patient_db[current_global_id]) + (0.1 * new_vector)

            # --- DRAWING ---
            global_display_id = active_track_map.get(track_id, "?")
            
            # Map Logic
            foot_x, foot_y = int((x1 + x2) / 2), int(y2)
            p = np.array([[[foot_x, foot_y]]], dtype=np.float32)
            transformed = cv2.perspectiveTransform(p, matrix)
            map_x, map_y = int(transformed[0][0][0]), int(transformed[0][0][1])

            # Draw
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"P{global_display_id}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
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