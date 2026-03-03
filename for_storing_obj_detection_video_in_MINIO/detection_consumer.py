import json
import base64
from kafka import KafkaConsumer
from minio import Minio
from minio.error import S3Error
from io import BytesIO
from datetime import datetime

# Kafka Configuration
KAFKA_BROKER = 'localhost:29092'
TOPIC_NAME = 'video-detection-segments'
GROUP_ID = 'detection-consumer-group'

# MinIO Configuration
MINIO_ENDPOINT = 'localhost:9000'
MINIO_ACCESS_KEY = 'minioadmin'
MINIO_SECRET_KEY = 'minioadmin'
BUCKET_NAME = 'camera-detections'

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
    enable_auto_commit=True,
    max_partition_fetch_bytes=52428800  # 50MB
)

print("Detection consumer started. Waiting for annotated video segments...")

try:
    for message in consumer:
        video_data = message.value
        
        segment_id = video_data['segment_id']
        timestamp = video_data['timestamp']
        duration = video_data['duration']
        frame_count = video_data['frame_count']
        detections = video_data.get('detections', {})
        video_base64 = video_data['video_data']
        
        print(f"\n{'='*60}")
        print(f"Received segment {segment_id}")
        print(f"Duration: {duration}s | Frames: {frame_count}")
        print(f"Detected objects: {detections}")
        print(f"{'='*60}")
        
        # Decode base64 video
        video_bytes = base64.b64decode(video_base64)
        video_size_mb = len(video_bytes) / (1024 * 1024)
        
        print(f"Video size: {video_size_mb:.2f} MB")
        
        # Create object name with timestamp
        dt = datetime.fromtimestamp(timestamp)
        object_name = f"detections/{dt.strftime('%Y%m%d')}/segment_{segment_id}_{dt.strftime('%H%M%S')}.mp4"
        
        # Create metadata JSON with detection info
        metadata_name = f"detections/{dt.strftime('%Y%m%d')}/segment_{segment_id}_{dt.strftime('%H%M%S')}_metadata.json"
        metadata = {
            'segment_id': segment_id,
            'timestamp': timestamp,
            'datetime': dt.isoformat(),
            'duration': duration,
            'frame_count': frame_count,
            'detections': detections,
            'video_file': object_name
        }
        
        # Upload video to MinIO
        try:
            print("Uploading video to MinIO...")
            minio_client.put_object(
                BUCKET_NAME,
                object_name,
                BytesIO(video_bytes),
                length=len(video_bytes),
                content_type='video/mp4'
            )
            print(f"✓ Video stored: {object_name}")
            
            # Upload metadata JSON
            metadata_bytes = json.dumps(metadata, indent=2).encode('utf-8')
            minio_client.put_object(
                BUCKET_NAME,
                metadata_name,
                BytesIO(metadata_bytes),
                length=len(metadata_bytes),
                content_type='application/json'
            )
            print(f"✓ Metadata stored: {metadata_name}")
            
        except S3Error as e:
            print(f"Error storing segment {segment_id}: {e}")
            
except KeyboardInterrupt:
    print("\nStopping consumer...")
finally:
    consumer.close()
    print("Consumer closed")