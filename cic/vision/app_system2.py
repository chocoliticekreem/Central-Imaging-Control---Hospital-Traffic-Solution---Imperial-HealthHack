import cv2
import numpy as np
from ultralytics import YOLO
import torch
import torchvision.transforms as T
import torchvision.models as models
from scipy.spatial.distance import cosine
import json
import threading
from flask import Flask, render_template, jsonify, Response

# --- 1. SETUP FLASK SERVER ---
app = Flask(__name__)

# Global variables to share data between AI (Thread A) and Web Server (Thread B)
live_patient_data = {} 
output_map_frame = None # Stores the latest map image for streaming
data_lock = threading.Lock() # Ensures threads don't clash

# Load the dummy EPR records
with open('cic/vision/patients.json', 'r') as f:
    epr_database = json.load(f)

@app.route('/')
def index():
    return render_template('index2.html')

@app.route('/data')
def get_data():
    """API endpoint for live text data"""
    return jsonify(live_patient_data)

def generate_map_feed():
    """Generator function that yields the map image as a stream"""
    global output_map_frame
    while True:
        with data_lock:
            if output_map_frame is None:
                continue
            # Encode the image to JPEG
            (flag, encodedImage) = cv2.imencode(".jpg", output_map_frame)
            if not flag:
                continue
        # Yield the output in MJPEG format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
              bytearray(encodedImage) + b'\r\n')

@app.route('/map_feed')
def map_feed():
    """Route for the Image tag to source"""
    return Response(generate_map_feed(),
                    mimetype = "multipart/x-mixed-replace; boundary=frame")

def run_flask():
    # Running on Port 5001 to avoid AirPlay conflict
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

# Start Flask in a separate thread
flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# --- 2. SETUP AI & COMPUTER VISION ---
device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
print(f"--- SYSTEM ONLINE ---")
print(f"AI Processor: {device}")
print(f"Mobile Dashboard: http://localhost:5001")

# Re-ID Model
feature_extractor = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)
feature_extractor = torch.nn.Sequential(*(list(feature_extractor.children())[:-1]))
feature_extractor.to(device)
feature_extractor.eval()

preprocess = T.Compose([
    T.ToPILImage(), T.Resize((224, 224)), T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

yolo_model = YOLO('yolov8n.pt') 

# Map Settings
MAP_WIDTH, MAP_HEIGHT = 600, 600
map_img = np.zeros((MAP_HEIGHT, MAP_WIDTH, 3), dtype=np.uint8)

# --- CALIBRATION (1920x1080 Mirrored) ---
src_points = np.float32([
    [817, 719],  # Top-Left
    [1441, 756],  # Top-Right
    [1664, 1072],  # Bottom-Right
    [216, 1068]   # Bottom-Left
])
# Mirrored Map Destination Points (Left on screen = Left on map)
dst_points = np.float32([
    [0, MAP_HEIGHT], [MAP_WIDTH, MAP_HEIGHT],
    [MAP_WIDTH, 0], [0, 0]
])
matrix = cv2.getPerspectiveTransform(src_points, dst_points)

# Data Stores
patient_fingerprints = {} 
next_global_id = 1
MATCH_THRESHOLD = 0.20
active_track_map = {} 

def get_embedding(image_crop):
    img_tensor = preprocess(image_crop).unsqueeze(0).to(device)
    with torch.no_grad(): features = feature_extractor(img_tensor)
    return features.cpu().numpy().flatten()

def identify_patient(image_crop):
    global next_global_id
    curr_vector = get_embedding(image_crop)
    best_id, lowest_dist = None, 1.0 
    
    for pid, saved_vector in patient_fingerprints.items():
        dist = cosine(curr_vector, saved_vector)
        if dist < lowest_dist: lowest_dist = dist; best_id = pid
            
    if lowest_dist < MATCH_THRESHOLD:
        return best_id, True, curr_vector
    else:
        new_id = next_global_id; next_global_id += 1
        return new_id, False, curr_vector

# --- 3. MAIN LOOP ---
cap = cv2.VideoCapture(0)
cap.set(3, 1920); cap.set(4, 1080)

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1) # Mirror Feed
    
    # Create the map for this frame
    current_map = map_img.copy()
    cv2.rectangle(current_map, (0,0), (MAP_WIDTH, MAP_HEIGHT), (255, 255, 255), -1)
    
    # Draw floor zone on camera
    cv2.polylines(frame, [np.int32(src_points)], True, (0, 255, 255), 2)

    results = yolo_model.track(frame, persist=True, classes=[0], verbose=False)
    current_frame_data = {}

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.int().cpu().numpy()

        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = map(int, box)
            
            # Re-ID Logic
            h, w, _ = frame.shape
            face_crop = frame[max(0,y1):min(h,y2), max(0,x1):min(w,x2)]
            
            if face_crop.size > 0:
                if track_id not in active_track_map:
                    global_id, _, vector = identify_patient(face_crop)
                    active_track_map[track_id] = global_id
                    patient_fingerprints[global_id] = vector
                
                gid = active_track_map[track_id]
                new_vec = get_embedding(face_crop)
                patient_fingerprints[gid] = (0.9 * patient_fingerprints[gid]) + (0.1 * new_vec)

            # Map Logic
            gid = active_track_map.get(track_id, 1)
            foot_x, foot_y = int((x1 + x2) / 2), int(y2)
            p = np.array([[[foot_x, foot_y]]], dtype=np.float32)
            transformed = cv2.perspectiveTransform(p, matrix)
            map_x, map_y = int(transformed[0][0][0]), int(transformed[0][0][1])

            # Sync to EPR
            epr_index = (gid - 1) % len(epr_database)
            epr_record = epr_database[epr_index]
            
            # Package Data
            current_frame_data[gid] = {
                "name": epr_record['name'],
                "epr_id": epr_record['epr_id'],
                "age": epr_record['age'],
                "condition": epr_record['condition'],
                "triage_score": epr_record['triage_score'],
                "notes": epr_record['notes'],
                "map_x": map_x,
                "map_y": map_y
            }

            # Draw on Camera
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{epr_record['name']}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            
            # Draw on Map
            if 0 <= map_x < MAP_WIDTH and 0 <= map_y < MAP_HEIGHT:
                cv2.circle(current_map, (map_x, map_y), 15, (255, 0, 0), -1)
                cv2.putText(current_map, f"{epr_record['name']}", (map_x+20, map_y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    # Update Global Variables for Flask
    live_patient_data = current_frame_data
    with data_lock:
        output_map_frame = current_map.copy()

    cv2.imshow("Main System", frame)
    cv2.imshow("2D Map", current_map) # Optional: Hide local map to save screen space

    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()