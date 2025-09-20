import os
from typing import Optional

try:
    import boto3
except Exception:
    boto3 = None  # Render上でrequirementsに入っていればOK。無くても未設定なら動く

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "")
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "")
S3_SECURE = os.getenv("S3_SECURE", "true").lower() == "true"

def is_s3_configured() -> bool:
    return all([S3_BUCKET, S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY]) and boto3 is not None

def _client():
    if not is_s3_configured():
        raise RuntimeError("S3 is not configured")
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        region_name=S3_REGION,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        use_ssl=S3_SECURE,
    )

def ensure_bucket() -> bool:
    """S3が設定済みの時だけバケット存在確認/作成する。未設定ならFalse返して何もしない。"""
    if not is_s3_configured():
        return False
    s3 = _client()
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
    except Exception:
        s3.create_bucket(Bucket=S3_BUCKET)
    return True

def presign_put(key: str, content_type: str, expires: int = 600) -> str:
    if not is_s3_configured():
        raise RuntimeError("S3 is not configured")
    s3 = _client()
    return s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": S3_BUCKET, "Key": key, "ContentType": content_type},
        ExpiresIn=expires,
    )

def presign_get(key: str, expires: int = 600) -> str:
    if not is_s3_configured():
        raise RuntimeError("S3 is not configured")
    s3 = _client()
    return s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )
