import os
from fastapi import APIRouter, Depends, HTTPException, status

from app.services.auth import get_current_user, get_access_token, get_user_id
from app.services.supabase_client import get_supabase_client, get_service_role_client

router = APIRouter(prefix="/storage")


def _is_dev_env() -> bool:
    env = (os.getenv("APP_ENV") or os.getenv("ENVIRONMENT") or os.getenv("FASTAPI_ENV") or "").lower()
    debug = (os.getenv("DEBUG") or "").lower() in ("1", "true", "yes")
    return env in ("dev", "development", "local") or debug


@router.get("/health")
def storage_health(user=Depends(get_current_user), token=Depends(get_access_token)):
    if not _is_dev_env():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    user_id = get_user_id(user)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalido")

    bucket = os.getenv("SUPABASE_STORAGE_BUCKET", "videos")
    client = get_supabase_client(token)

    bucket_exists = None
    bucket_error = None

    try:
        admin = get_service_role_client()
        buckets = admin.storage.list_buckets()
        bucket_exists = any(
            (b.get("name") if isinstance(b, dict) else getattr(b, "name", None)) == bucket
            for b in (buckets or [])
        )
    except Exception as exc:
        bucket_error = str(exc)

    list_ok = False
    list_error = None
    objects = None

    try:
        objects = client.storage.from_(bucket).list(path=f"{user_id}/", limit=10)
        list_ok = True
    except Exception as exc:
        list_error = str(exc)

    return {
        "bucket": bucket,
        "bucket_exists": bucket_exists,
        "bucket_error": bucket_error,
        "user_prefix": f"{user_id}/",
        "list_ok": list_ok,
        "list_error": list_error,
        "sample": objects,
    }