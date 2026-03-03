import cv2
import json
import time
from kafka import KafkaProducer
import base64
import tempfile
import os
from ultralytics import YOLO

# Kafka Configuration
KAFKA_BROKER = 'localhost:29092'
TOPIC_NAME = 'video-detection-segments'

# Video Configuration
SEGMENT_DURATION = 60  # 1 minutes in seconds
FPS = 20
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# YOLOv8 Configuration
print("Loading YOLOv26 medium model...")
model = YOLO('yolo26m.pt')  # Downloads model on first run
print("Model loaded successfully!")

# Initialize Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    max_request_size=52428800  # 50MB
)

# Initialize Camera
camera = cv2.VideoCapture(0)
camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
camera.set(cv2.CAP_PROP_FPS, FPS)

if not camera.isOpened():
    print("Error: Could not open camera")
    exit()

print(f"Starting object detection - {SEGMENT_DURATION}s segments at {FPS} FPS...")
segment_count = 0

try:
    while True:
        segment_count += 1
        start_time = time.time()
        
        # Create temporary video file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        temp_path = temp_file.name
        temp_file.close()
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(temp_path, fourcc, FPS, (FRAME_WIDTH, FRAME_HEIGHT))
        
        print(f"\n=== Recording Segment {segment_count} with Object Detection ===")
        frame_count = 0
        detection_summary = {}
        
        # Record for SEGMENT_DURATION seconds
        while (time.time() - start_time) < SEGMENT_DURATION:
            ret, frame = camera.read()
            
            if not ret:
                print("Failed to capture frame")
                break
            
            # Run YOLOv8 detection
            results = model(frame, verbose=False, conf=0.5)
            
            # Draw detections on frame
            annotated_frame = results[0].plot()
            
            # Count detected objects
            for box in results[0].boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                detection_summary[class_name] = detection_summary.get(class_name, 0) + 1
            
            writer.write(annotated_frame)
            frame_count += 1
            
            # Progress indicator every second
            if frame_count % FPS == 0:
                elapsed = int(time.time() - start_time)
                remaining = SEGMENT_DURATION - elapsed
                print(f"Recording... {elapsed}s / {SEGMENT_DURATION}s (remaining: {remaining}s)", end='\r')
        
        writer.release()
        print(f"\nSegment {segment_count} recorded: {frame_count} frames")
        print(f"Detections summary: {detection_summary}")
        
        # Read video file and encode to base64
        with open(temp_path, 'rb') as f:
            video_data = f.read()
        
        video_base64 = base64.b64encode(video_data).decode('utf-8')
        file_size_mb = len(video_data) / (1024 * 1024)
        
        print(f"Encoded video size: {file_size_mb:.2f} MB")
        
        # Create message payload with detection metadata
        message = {
            'segment_id': segment_count,
            'timestamp': start_time,
            'duration': SEGMENT_DURATION,
            'fps': FPS,
            'frame_count': frame_count,
            'detections': detection_summary,
            'video_data': video_base64
        }
        
        # Send to Kafka
        print("Sending to Kafka...")
        producer.send(TOPIC_NAME, value=message)
        producer.flush()
        print(f"✓ Segment {segment_count} sent to Kafka")
        
        # Clean up temp file
        os.unlink(temp_path)
        
except KeyboardInterrupt:
    print("\n\nStopping producer...")
finally:
    camera.release()
    producer.close()
    print("Producer closed")