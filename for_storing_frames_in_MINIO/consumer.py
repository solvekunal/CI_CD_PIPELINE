import json
import base64
from kafka import KafkaConsumer
from minio import Minio
from minio.error import S3Error
from io import BytesIO
from datetime import datetime

# Kafka Configuration
# KAFKA_BROKER = 'localhost:9092'
KAFKA_BROKER = 'localhost:29092'  # Change from 9092 to 29092
TOPIC_NAME = 'camera-frames'
GROUP_ID = 'frame-consumer-group'

# MinIO Configuration
MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin'
BUCKET_NAME = 'camera-frames'

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

# Create bucket if it doesn't exist
try:
    if not minio_client.bucket_exists(BUCKET_NAME):
        minio_client.make_bucket(BUCKET_NAME)
        print(f"Bucket '{BUCKET_NAME}' created")
    else:
        print(f"Bucket '{BUCKET_NAME}' already exists")
except S3Error as e:
    print(f"Error creating bucket: {e}")

# Initialize Kafka Consumer
consumer = KafkaConsumer(
    TOPIC_NAME,
    bootstrap_servers=[KAFKA_BROKER],
    group_id=GROUP_ID,
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='latest',
    enable_auto_commit=True
)

print("Consumer started. Waiting for messages...")

try:
    for message in consumer:
        frame_data = message.value
        
        frame_id = frame_data['frame_id']
        timestamp = frame_data['timestamp']
        image_base64 = frame_data['image_data']
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_base64)
        
        # Create object name with timestamp
        dt = datetime.fromtimestamp(timestamp)
        object_name = f"frames/{dt.strftime('%Y%m%d')}/frame_{frame_id}_{int(timestamp)}.jpg"
        
        # Upload to MinIO
        try:
            minio_client.put_object(
                BUCKET_NAME,
                object_name,
                BytesIO(image_bytes),
                length=len(image_bytes),
                content_type='image/jpeg'
            )
            print(f"Stored frame {frame_id} as {object_name}")
        except S3Error as e:
            print(f"Error storing frame {frame_id}: {e}")
            
except KeyboardInterrupt:
    print("\nStopping consumer...")
finally:
    consumer.close()
    print("Consumer closed")