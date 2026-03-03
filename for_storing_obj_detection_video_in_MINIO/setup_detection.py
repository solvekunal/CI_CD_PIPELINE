from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, NoBrokersAvailable
import time

# Kafka Configuration
KAFKA_BROKER = 'localhost:29092'
TOPIC_NAME = 'video-detection-segments'

# Retry logic for Kafka connection
max_retries = 10
retry_delay = 3

print("Waiting for Kafka brokers to be ready...")

for attempt in range(max_retries):
    try:
        # Initialize Kafka Admin Client
        admin_client = KafkaAdminClient(
            bootstrap_servers=[KAFKA_BROKER],
            client_id='setup-client',
            request_timeout_ms=10000
        )
        print("Successfully connected to Kafka broker!")
        break
    except (NoBrokersAvailable, Exception) as e:
        if attempt < max_retries - 1:
            print(f"Attempt {attempt + 1}/{max_retries}: Brokers not ready yet. Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print(f"Failed to connect after {max_retries} attempts. Please check if Docker containers are running.")
            print("Run: docker ps")
            exit(1)

# Define topic configuration for detection video segments
topic = NewTopic(
    name=TOPIC_NAME,
    num_partitions=1,
    replication_factor=1,
    topic_configs={
        'max.message.bytes': '52428800',  # 50MB
        'retention.ms': '86400000'  # 24 hours retention
    }
)

try:
    # Create topic
    admin_client.create_topics(new_topics=[topic], validate_only=False)
    print(f"Topic '{TOPIC_NAME}' created successfully")
except TopicAlreadyExistsError:
    print(f"Topic '{TOPIC_NAME}' already exists")
except Exception as e:
    print(f"Error creating topic: {e}")
finally:
    admin_client.close()