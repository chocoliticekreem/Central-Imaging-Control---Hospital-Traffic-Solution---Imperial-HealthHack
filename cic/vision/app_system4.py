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

# Global variables
live_patient_data = {} 
output_map_frame = None 
data_lock = threading.Lock() 

# Load records
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
print(f"AI Processor: {device}")
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

# --- NEW: SPLIT-BODY LOGIC ---
# Stores { global_id : {'top': vector, 'bot': vector} }
patient_fingerprints = {} 
next_global_id = 1
MATCH_THRESHOLD = 0.20
active_track_map = {} 

def get_split_embedding(image_crop):
    """
    Splits image into Top (Torso) and Bottom (Legs) and gets 2 vectors.
    """
    h, w, _ = image_crop.shape
    if h < 10 or w < 10: return None, None # Safety check for tiny crops
    
    # Crop top 50% and bottom 50%
    top_half = image_crop[0:int(h/2), :]
    bottom_half = image_crop[int(h/2):h, :]
    
    # Preprocess
    top_tensor = preprocess(top_half).unsqueeze(0).to(device)
    bot_tensor = preprocess(bottom_half).unsqueeze(0).to(device)
    
    # Extract Features
    with torch.no_grad():
        top_feat = feature_extractor(top_tensor).cpu().numpy().flatten()
        bot_feat = feature_extractor(bot_tensor).cpu().numpy().flatten()
        
    return top_feat, bot_feat

def identify_patient(image_crop):
    global next_global_id
    
    curr_top, curr_bot = get_split_embedding(image_crop)
    if curr_top is None: return None, False, None # Skip bad crops
    
    best_id = None
    lowest_dist = 1.0 
    
    for pid, saved_data in patient_fingerprints.items():
        saved_top = saved_data['top']
        saved_bot = saved_data['bot']
        
        dist_top = cosine(curr_top, saved_top)
        dist_bot = cosine(curr_bot, saved_bot)
        
        # WEIGHTING: 30% Top, 70% Bottom (Trust legs more)
        weighted_dist = (0.3 * dist_top) + (0.7 * dist_bot)
        
        if weighted_dist < lowest_dist:
            lowest_dist = weighted_dist
            best_id = pid
            
    # Return structure: ID, Is_Match, New_Vectors_Dict
    vectors = {'top': curr_top, 'bot': curr_bot}
            
    if lowest_dist < MATCH_THRESHOLD:
        return best_id, True, vectors
    else:
        new_id = next_global_id
        next_global_id += 1
        return new_id, False, vectors

def get_checkup_info(news2_score, patient_id):
    if news2_score >= 7: freq, label = 30, "HIGH RISK"
    elif news2_score >= 5: freq, label = 60, "MED RISK"
    elif news2_score >= 1: freq, label = 240, "LOW-MED"
    else: freq, label = 720, "LOW RISK"
    offset = (patient_id * 17) % freq 
    return label, freq - offset

# --- 3. MAIN LOOP ---
# Use 0 for Webcam, or 'demo_footage.mp4' for video file
cap = cv2.VideoCapture(0) 

while True:
    ret, frame = cap.read()
    if not ret: 
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
        continue

    # frame = cv2.resize(frame, (1920, 1080)) # Enable for 4K video
    frame = cv2.flip(frame, 1) 
    
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
                    global_id, _, vectors = identify_patient(face_crop)
                    if global_id:
                        active_track_map[track_id] = global_id
                        patient_fingerprints[global_id] = vectors
                
                # ADAPTIVE UPDATE (Update Top and Bottom separately)
                if track_id in active_track_map:
                    gid = active_track_map[track_id]
                    curr_top, curr_bot = get_split_embedding(face_crop)
                    
                    if curr_top is not None:
                        # Blend old and new (90% old, 10% new)
                        old_top = patient_fingerprints[gid]['top']
                        old_bot = patient_fingerprints[gid]['bot']
                        
                        patient_fingerprints[gid]['top'] = (0.9 * old_top) + (0.1 * curr_top)
                        patient_fingerprints[gid]['bot'] = (0.9 * old_bot) + (0.1 * curr_bot)

            # Map & Display Logic
            gid = active_track_map.get(track_id, 1)
            epr_index = (gid - 1) % len(epr_database)
            epr_record = epr_database[epr_index]
            
            risk_label, mins_left = get_checkup_info(epr_record['news2_score'], gid)

            foot_x, foot_y = int((x1 + x2) / 2), int(y2)
            p = np.array([[[foot_x, foot_y]]], dtype=np.float32)
            transformed = cv2.perspectiveTransform(p, matrix)
            map_x, map_y = int(transformed[0][0][0]), int(transformed[0][0][1])

            triage_text = epr_record['triage_score'].split()[0]
            dot_color = (255, 0, 0)
            if triage_text == "Red": dot_color = (0, 0, 255)
            elif triage_text == "Yellow": dot_color = (0, 255, 255)
            elif triage_text == "Green": dot_color = (0, 200, 0)

            current_frame_data[gid] = {
                "name": epr_record['name'],
                "epr_id": epr_record['epr_id'],
                "condition": epr_record['condition'],
                "triage_score": epr_record['triage_score'],
                "news2_score": epr_record['news2_score'],
                "risk_label": risk_label,
                "mins_remaining": mins_left,
                "map_x": map_x,
                "map_y": map_y
            }

            cv2.rectangle(frame, (x1, y1), (x2, y2), dot_color, 2)
            cv2.putText(frame, f"{epr_record['name']} ({risk_label})", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, dot_color, 2)
            
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