#!/usr/bin/env python3

import boto3
from botocore.exceptions import ClientError
from flask import current_app

class S3Repository:
    def __init__(self):
        self.client = boto3.client(
            's3',
            endpoint_url=current_app.config['S3_ENDPOINT'],
            aws_access_key_id=current_app.config['S3_ACCESS_KEY'],
            aws_secret_access_key=current_app.config['S3_SECRET_KEY'],
            region_name=current_app.config['S3_REGION']
        )
        self.bucket = current_app.config['S3_BUCKET_NAME']
        self._ensure_bucket()

    def _ensure_bucket(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)
            print(f"Created bucket: {self.bucket}")

    def upload_file(self, file_obj, key):
        try:
            self.client.upload_fileobj(file_obj, self.bucket, key)
            return True
        except ClientError as e:
            print(f"Upload error: {e}")
            return False

    def download_file(self, key):
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            return response['Body'].read()
        except ClientError as e:
            print(f"Download error: {e}")
            return None

    def delete_file(self, key):
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            print(f"Delete error: {e}")
            return False

    def generate_presigned_url(self, key, expiration=3600):
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            print(f"Presigned URL error: {e}")
            return None
