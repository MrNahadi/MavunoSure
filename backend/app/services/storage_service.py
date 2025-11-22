"""Storage service for file uploads"""

import base64
import uuid
from typing import Optional
from io import BytesIO
from app.config import settings


class StorageService:
    """Service for handling file storage operations"""
    
    def __init__(self):
        self.provider = settings.STORAGE_PROVIDER
        self.bucket = settings.AWS_S3_BUCKET
        self._s3_client = None
    
    @property
    def s3_client(self):
        """Lazy load S3 client"""
        if self._s3_client is None and self.provider == "s3":
            import boto3
            self._s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
        return self._s3_client
    
    def upload_claim_image(self, image_data: str, claim_id: uuid.UUID) -> str:
        """
        Upload claim image to storage
        
        Args:
            image_data: Base64 encoded image data
            claim_id: Unique claim identifier
            
        Returns:
            URL of uploaded image
        """
        # Decode base64 image
        try:
            # Remove data URL prefix if present
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            raise ValueError(f"Invalid image data: {str(e)}")
        
        # Generate unique filename
        filename = f"claims/{claim_id}/{uuid.uuid4()}.jpg"
        
        if self.provider == "s3":
            return self._upload_to_s3(image_bytes, filename)
        else:
            # For development/testing, store locally
            return self._upload_locally(image_bytes, filename)
    
    def _upload_to_s3(self, image_bytes: bytes, filename: str) -> str:
        """Upload image to S3"""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=filename,
                Body=image_bytes,
                ContentType='image/jpeg'
            )
            
            # Return S3 URL
            return f"https://{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
        except Exception as e:
            raise RuntimeError(f"Failed to upload to S3: {str(e)}")
    
    def _upload_locally(self, image_bytes: bytes, filename: str) -> str:
        """Upload image to local filesystem (for development)"""
        import os
        from pathlib import Path
        
        # Create uploads directory if it doesn't exist
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        file_path = upload_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        
        # Return local URL
        return f"/uploads/{filename}"
    
    def delete_image(self, image_url: str) -> bool:
        """
        Delete image from storage
        
        Args:
            image_url: URL of image to delete
            
        Returns:
            True if successful, False otherwise
        """
        if self.provider == "s3":
            try:
                # Extract key from URL
                key = image_url.split(f"{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/")[1]
                self.s3_client.delete_object(Bucket=self.bucket, Key=key)
                return True
            except Exception:
                return False
        else:
            # Delete local file
            try:
                import os
                file_path = image_url.replace("/uploads/", "uploads/")
                if os.path.exists(file_path):
                    os.remove(file_path)
                return True
            except Exception:
                return False


# Singleton instance
storage_service = StorageService()
