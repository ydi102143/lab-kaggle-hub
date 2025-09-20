import os
import boto3

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_REGION   = os.getenv("S3_REGION", "us-east-1")
S3_BUCKET   = os.getenv("S3_BUCKET", "lab-artifacts")
S3_ACCESS   = os.getenv("S3_ACCESS_KEY", "minio")
S3_SECRET   = os.getenv("S3_SECRET_KEY", "minio123")

def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS,
        aws_secret_access_key=S3_SECRET,
        region_name=S3_REGION,
        config=boto3.session.Config(signature_version="s3v4"),
    )

def ensure_bucket():
    s3 = s3_client()
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
    except Exception:
        s3.create_bucket(Bucket=S3_BUCKET)

def presign_put(key: str, expires=3600):
    s3 = s3_client()
    return s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )

def presign_get(key: str, expires=3600):
    s3 = s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )
