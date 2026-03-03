# MinIO to AWS S3 Migration Guide

When deploying to AWS production, you only need to change the MinIO client configuration. The code structure remains identical.

## Current MinIO Configuration (Development)

```python
from minio import Minio

minio_client = Minio(
    'localhost:9000',
    access_key='minioadmin',
    secret_key='minioadmin',
    secure=False
)
```

## AWS S3 Configuration (Production)

### Option 1: Direct S3 Connection
```python
from minio import Minio

s3_client = Minio(
    's3.amazonaws.com',  # or 's3.us-east-1.amazonaws.com' for specific region
    access_key='YOUR_AWS_ACCESS_KEY',
    secret_key='YOUR_AWS_SECRET_KEY',
    secure=True,
    region='us-east-1'  # your AWS region
)
```

### Option 2: Using Environment Variables (Recommended)
```python
import os
from minio import Minio

s3_client = Minio(
    os.getenv('S3_ENDPOINT', 's3.amazonaws.com'),
    access_key=os.getenv('AWS_ACCESS_KEY_ID'),
    secret_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    secure=True,
    region=os.getenv('AWS_REGION', 'us-east-1')
)
```

### Option 3: Using AWS IAM Roles (Best for EC2/ECS/Lambda)
```python
import boto3
from minio import Minio

# When running on AWS services with IAM roles, boto3 automatically uses IAM credentials
session = boto3.Session()
credentials = session.get_credentials()

s3_client = Minio(
    's3.amazonaws.com',
    access_key=credentials.access_key,
    secret_key=credentials.secret_key,
    session_token=credentials.token,  # Required for temporary credentials
    secure=True,
    region='us-east-1'
)
```

## Complete Example: Environment-based Configuration

Create a `config.py` file:

```python
import os
from minio import Minio

def get_storage_client():
    """
    Returns MinIO client for local dev or S3 client for production
    Based on environment variable ENVIRONMENT
    """
    environment = os.getenv('ENVIRONMENT', 'development')
    
    if environment == 'production':
        # AWS S3 Production
        return Minio(
            os.getenv('S3_ENDPOINT', 's3.amazonaws.com'),
            access_key=os.getenv('AWS_ACCESS_KEY_ID'),
            secret_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            secure=True,
            region=os.getenv('AWS_REGION', 'us-east-1')
        )
    else:
        # MinIO Development
        return Minio(
            os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
            access_key=os.getenv('MINIO_ACCESS_KEY', 'minioadmin'),
            secret_key=os.getenv('MINIO_SECRET_KEY', 'minioadmin'),
            secure=False
        )

# Bucket name (same for both environments)
BUCKET_NAME = os.getenv('BUCKET_NAME', 'camera-detections')
```

Then in your consumer code:

```python
from config import get_storage_client, BUCKET_NAME

# This works for both MinIO and S3!
storage_client = get_storage_client()

# All operations remain identical
storage_client.bucket_exists(BUCKET_NAME)
storage_client.make_bucket(BUCKET_NAME)
storage_client.put_object(BUCKET_NAME, object_name, data, length, content_type)
```

## Environment Variables for Production

Set these in your AWS deployment (EC2, ECS, Lambda, etc.):

```bash
export ENVIRONMENT=production
export S3_ENDPOINT=s3.amazonaws.com
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=us-east-1
export BUCKET_NAME=camera-detections
export KAFKA_BROKER=your-kafka-broker:9092
```

## AWS S3 Bucket Creation

Before deploying, create S3 buckets:

```bash
aws s3 mb s3://camera-detections --region us-east-1
```

Or using boto3:

```python
import boto3

s3 = boto3.client('s3', region_name='us-east-1')
s3.create_bucket(Bucket='camera-detections')
```

## IAM Policy for S3 Access

Attach this policy to your AWS IAM role/user:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::camera-detections",
        "arn:aws:s3:::camera-detections/*"
      ]
    }
  ]
}
```

## Key Differences: MinIO vs S3

| Feature | MinIO | AWS S3 |
|---------|-------|--------|
| Endpoint | localhost:9000 | s3.amazonaws.com |
| Secure | False | True |
| Region | Not required | Required |
| Credentials | Static (minioadmin) | AWS IAM or Access Keys |
| Cost | Free (self-hosted) | Pay per storage/requests |

## No Code Changes Required!

The MinIO Python client is S3-compatible. All these operations work identically:
- `bucket_exists()`
- `make_bucket()`
- `put_object()`
- `get_object()`
- `list_objects()`
- `remove_object()`

Only the client initialization changes!