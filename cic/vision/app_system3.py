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
import time

# --- 1. SETUP FLASK SERVER ---
app = Flask(__name__)

# Global variables
live_patient_data = {} 
output_map_frame = None 
data_lock = threading.Lock() 

# Load dummy records
with open('cic/vision/patients.json', 'r') as f:
    epr_database = json.load(f)

@app.route('/')
def index():
    return render_template('index3.html')

@app.route('/data')
def get_data():
    return jsonify(live_patient_data)

def generate_map_feed():
    global output_map_frame
    while True:
        with data_lock:
            if output_map_frame is None:
                continue
            (flag, encodedImage) = cv2.imencode(".jpg", output_map_frame)
            if not flag:
                continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
              bytearray(encodedImage) + b'\r\n')

@app.route('/map_feed')
def map_feed():
    return Response(generate_map_feed(),
                    mimetype = "multipart/x-mixed-replace; boundary=frame")

def run_flask():
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)

flask_thread = threading.Thread(target=run_flask)
flask_thread.daemon = True
flask_thread.start()

# --- 2. SETUP AI ---
device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
print(f"--- SYSTEM ONLINE ---")
print(f"Mobile Dashboard: http://localhost:5001")

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
MAP_WIDTH, MAP_HEIGHT = 500, 500
map_img = np.zeros((MAP_HEIGHT, MAP_WIDTH, 3), dtype=np.uint8)

# CALIBRATION
src_points = np.float32([
    [817, 719],  # Top-Left
    [1441, 756],  # Top-Right
    [1664, 1072],  # Bottom-Right
    [216, 1068]   # Bottom-Left
])
dst_points = np.float32([
    [0, MAP_HEIGHT], [MAP_WIDTH, MAP_HEIGHT],
    [MAP_WIDTH, 0], [0, 0]
])
matrix = cv2.getPerspectiveTransform(src_points, dst_points)

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

def get_checkup_info(news2_score, patient_id):
    """
    Calculates the frequency and a dummy 'time remaining' based on NEWS2.
    """
    # 1. Determine Frequency Rule (in minutes)
    if news2_score >= 7:
        freq_mins = 30         # High Risk: 30 mins
        risk_label = "HIGH RISK"
    elif news2_score >= 5:
        freq_mins = 60         # Medium Risk: Hourly
        risk_label = "MED RISK"
    elif news2_score >= 1:
        freq_mins = 240        # Low-Med Risk: 4 hours
        risk_label = "LOW-MED"
    else:
        freq_mins = 720        # Low Risk: 12 hours
        risk_label = "LOW RISK"

    # 2. Simulate "Time Remaining" for the demo
    # We use the patient_id to make a fixed "random" offset so it looks consistent
    # e.g., Patient 1 always has 15 mins left, Patient 2 has 45 mins left.
    offset = (patient_id * 17) % freq_mins 
    mins_remaining = freq_mins - offset
    
    return risk_label, mins_remaining

# --- 3. MAIN LOOP ---
# UPDATE: Change 'demo_footage.mp4' back to 0 if using webcam
cap = cv2.VideoCapture(0) 

while True:
    ret, frame = cap.read()
    
    if not ret: 
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        continue

    # frame = cv2.resize(frame, (1920, 1080)) # Enable if video is 4K
    frame = cv2.flip(frame, 1) # Mirroring
    
    current_map = map_img.copy()
    cv2.rectangle(current_map, (0,0), (MAP_WIDTH, MAP_HEIGHT), (255, 255, 255), -1)
    cv2.polylines(frame, [np.int32(src_points)], True, (0, 255, 255), 2)

    results = yolo_model.track(frame, persist=True, classes=[0], verbose=False)
    current_frame_data = {}

    if results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        track_ids = results[0].boxes.id.int().cpu().numpy()

        for box, track_id in zip(boxes, track_ids):
            x1, y1, x2, y2 = map(int, box)
            
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

            gid = active_track_map.get(track_id, 1)
            
            # Get EPR Data
            epr_index = (gid - 1) % len(epr_database)
            epr_record = epr_database[epr_index]
            
            # --- CALCULATE NEWS2 DATA ---
            risk_label, mins_left = get_checkup_info(epr_record['news2_score'], gid)
            # ----------------------------

            # Map Math
            foot_x, foot_y = int((x1 + x2) / 2), int(y2)
            p = np.array([[[foot_x, foot_y]]], dtype=np.float32)
            transformed = cv2.perspectiveTransform(p, matrix)
            map_x, map_y = int(transformed[0][0][0]), int(transformed[0][0][1])

            # Color Logic
            triage_text = epr_record['triage_score'].split()[0]
            dot_color = (255, 0, 0)
            if triage_text == "Red": dot_color = (0, 0, 255)
            elif triage_text == "Yellow": dot_color = (0, 255, 255)
            elif triage_text == "Green": dot_color = (0, 200, 0)

            # Package Data
            current_frame_data[gid] = {
                "name": epr_record['name'],
                "epr_id": epr_record['epr_id'],
                "condition": epr_record['condition'],
                "triage_score": epr_record['triage_score'],
                "news2_score": epr_record['news2_score'], # Needed for sorting
                "risk_label": risk_label,                 # Needed for timer
                "mins_remaining": mins_left,              # Needed for timer
                "map_x": map_x,
                "map_y": map_y
            }

            # Draw on Camera
            cv2.rectangle(frame, (x1, y1), (x2, y2), dot_color, 2)
            cv2.putText(frame, f"{epr_record['name']} ({risk_label})", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, dot_color, 2)
            
            # Draw on Map
            if 0 <= map_x < MAP_WIDTH and 0 <= map_y < MAP_HEIGHT:
                cv2.circle(current_map, (map_x, map_y), 15, dot_color, -1)
                cv2.putText(current_map, f"{epr_record['name']}", (map_x+20, map_y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

    live_patient_data = current_frame_data
    with data_lock:
        output_map_frame = current_map.copy()

    cv2.imshow("Main System", frame)
    cv2.imshow("2D Map", current_map) 

    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()