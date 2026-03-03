# import cv2
# import json
# import time
# from kafka import KafkaProducer
# import base64

# # Kafka Configuration
# KAFKA_BROKER = 'localhost:9092'
# TOPIC_NAME = 'camera-frames'

# # Initialize Kafka Producer
# producer = KafkaProducer(
#     bootstrap_servers=[KAFKA_BROKER],
#     value_serializer=lambda v: json.dumps(v).encode('utf-8'),
#     max_request_size=10485760  # 10MB for large images
# )

# # Initialize Camera
# camera = cv2.VideoCapture(0)

# if not camera.isOpened():
#     print("Error: Could not open camera")
#     exit()

# print("Starting frame capture and sending to Kafka...")
# frame_count = 0

# try:
#     while True:
#         ret, frame = camera.read()
        
#         if not ret:
#             print("Failed to capture frame")
#             break
        
#         # Encode frame to JPEG
#         _, buffer = cv2.imencode('.jpg', frame)
        
#         # Convert to base64 for JSON serialization
#         frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
#         # Create message payload
#         message = {
#             'frame_id': frame_count,
#             'timestamp': time.time(),
#             'image_data': frame_base64
#         }
        
#         # Send to Kafka
#         producer.send(TOPIC_NAME, value=message)
        
#         frame_count += 1
#         print(f"Sent frame {frame_count}")
        
#         # Capture at ~10 FPS
#         time.sleep(0.1)
        
# except KeyboardInterrupt:
#     print("\nStopping producer...")
# finally:
#     camera.release()
#     producer.flush()
#     producer.close()
#     print("Producer closed")








import cv2
import json
import time
from kafka import KafkaProducer
import base64

# Kafka Configuration
KAFKA_BROKER = 'localhost:29092'
TOPIC_NAME = 'camera-frames'

# Initialize Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BROKER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    max_request_size=10485760  # 10MB for large images
)

# Initialize Camera
camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("Error: Could not open camera")
    exit()

print("Starting frame capture and sending to Kafka...")
frame_count = 0

try:
    while True:
        ret, frame = camera.read()
        
        if not ret:
            print("Failed to capture frame")
            break
        
        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        
        # Convert to base64 for JSON serialization
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Create message payload
        message = {
            'frame_id': frame_count,
            'timestamp': time.time(),
            'image_data': frame_base64
        }
        
        # Send to Kafka
        producer.send(TOPIC_NAME, value=message)
        
        frame_count += 1
        print(f"Sent frame {frame_count}")
        
        # Capture at ~10 FPS
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\nStopping producer...")
finally:
    camera.release()
    producer.flush()
    producer.close()
    print("Producer closed")