import os
import uuid
import structlog
from supabase import create_client, Client
from app.core.config import settings

logger = structlog.get_logger(__name__)

class SupabaseStorageService:
    def __init__(self):
        try:
            self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            self.bucket_name = "leaf-scans"
        except Exception as e:
            logger.error("supabase_init_failed", error=str(e))
            self.client = None

    async def upload_leaf_scan(self, user_id: str, field_id: str, image_bytes: bytes, content_type: str) -> str:
        """
        Uploads a leaf scan image to Supabase Storage.
        Format: leaf-scans/{user_id}/{field_id}/{uuid}.jpg
        """
        if not self.client:
            logger.warning("Supabase client not initialized, skipping upload")
            return "mock_storage_path.jpg"
            
        file_ext = "jpg"
        if content_type == "image/png":
            file_ext = "png"
            
        file_name = f"{uuid.uuid4()}.{file_ext}"
        storage_path = f"{user_id}/{field_id}/{file_name}"
        
        try:
            # Note: The supabase-python storage API is synchronous. For high throughput,
            # we should wrap this in asyncio.to_thread in the caller.
            res = self.client.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=image_bytes,
                file_options={"content-type": content_type}
            )
            logger.info("supabase_upload_success", path=storage_path)
            
            # For now, we store the internal storage path. 
            # We can generate signed URLs dynamically when the frontend requests it.
            return storage_path
            
        except Exception as e:
            logger.error("supabase_upload_failed", error=str(e), path=storage_path)
            # Throw or return none based on strictness. Let's return a fallback for dev.
            return f"failed_upload/{storage_path}"

supabase_storage = SupabaseStorageService()
