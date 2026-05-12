from supabase import create_client, Client
from dotenv import load_dotenv
import os
import structlog

log = structlog.get_logger()
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "PASTE_YOUR_SUPABASE_URL_HERE")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "PASTE_YOUR_SUPABASE_SERVICE_KEY_HERE")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "PASTE_YOUR_SUPABASE_ANON_KEY_HERE")

# Service client (bypasses RLS — for backend ML operations)
_service_client: Client = None
# Anon client (respects RLS — for user operations)
_anon_client: Client = None

def get_db() -> Client:
    global _service_client
    if _service_client is None:
        _service_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _service_client

def get_anon_db() -> Client:
    global _anon_client
    if _anon_client is None:
        _anon_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _anon_client

def db_insert(table: str, data: dict) -> dict:
    try:
        db = get_db()
        response = db.table(table).insert(data).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        log.error("db_insert_error", table=table, error=str(e))
        raise

def db_select(table: str, filters: dict = None, limit: int = 100) -> list:
    try:
        db = get_db()
        query = db.table(table).select("*")
        if filters:
            for k, v in filters.items():
                query = query.eq(k, v)
        response = query.limit(limit).execute()
        return response.data
    except Exception as e:
        log.error("db_select_error", table=table, error=str(e))
        return []

def db_update(table: str, id: str, data: dict) -> dict:
    try:
        db = get_db()
        response = db.table(table).update(data).eq("id", id).execute()
        return response.data[0] if response.data else {}
    except Exception as e:
        log.error("db_update_error", table=table, id=id, error=str(e))
        raise

def db_select_one(table: str, filters: dict) -> dict | None:
    try:
        db = get_db()
        query = db.table(table).select("*")
        for k, v in filters.items():
            query = query.eq(k, v)
        response = query.limit(1).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        log.error("db_select_one_error", table=table, error=str(e))
        return None

def storage_upload(bucket: str, path: str, file_bytes: bytes, content_type: str = "image/jpeg") -> str:
    try:
        db = get_db()
        # Ensure path doesn't start with /
        if path.startswith("/"):
            path = path[1:]
        res = db.storage.from_(bucket).upload(
            path, 
            file_bytes, 
            file_options={"content-type": content_type, "upsert": "true"}
        )
        # Assuming the bucket is public, generate the public URL
        url = db.storage.from_(bucket).get_public_url(path)
        return url
    except Exception as e:
        log.error("storage_upload_error", bucket=bucket, path=path, error=str(e))
        raise

def storage_get_url(bucket: str, path: str) -> str:
    try:
        db = get_db()
        if path.startswith("/"):
            path = path[1:]
        return db.storage.from_(bucket).get_public_url(path)
    except Exception as e:
        log.error("storage_get_url_error", bucket=bucket, path=path, error=str(e))
        return ""
