import os
import tempfile
from typing import Any
import requests

from app.services.supabase_client import get_service_role_client


def normalize_storage_path(value: str | None, bucket: str) -> str | None:
    if not value:
        return None
    normalized = value.strip()

    public_marker = f"/storage/v1/object/public/{bucket}/"
    signed_marker = f"/storage/v1/object/sign/{bucket}/"

    if public_marker in normalized:
        return normalized.split(public_marker, 1)[1].split("?", 1)[0]
    if signed_marker in normalized:
        return normalized.split(signed_marker, 1)[1].split("?", 1)[0]

    # Caminho local (uploads/ ou caminho absoluto no Windows)
    if normalized.startswith("uploads") or "\\" in normalized or ":" in normalized:
        return None

    if normalized.startswith(f"{bucket}/"):
        return normalized[len(bucket) + 1 :]

    return normalized


def _extract_signed_url(result: Any) -> str | None:
    if result is None:
        return None
    if isinstance(result, dict):
        return result.get("signedURL") or result.get("signedUrl") or result.get("signed_url")
    return getattr(result, "signedURL", None) or getattr(result, "signedUrl", None) or getattr(result, "signed_url", None)


def create_signed_url(bucket: str, path: str, expires_in: int = 300) -> str:
    client = get_service_role_client()
    result = client.storage.from_(bucket).create_signed_url(path, expires_in)
    signed_url = _extract_signed_url(result)
    if not signed_url:
        raise RuntimeError("Falha ao gerar signed URL para o Storage.")
    return signed_url


def download_storage_file(
    bucket: str,
    path: str,
    expires_in: int = 300,
    timeout: int = 60,
    suffix: str | None = None,
) -> str:
    signed_url = create_signed_url(bucket, path, expires_in=expires_in)

    if not suffix:
        suffix = os.path.splitext(path)[1] or ".bin"

    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as handle:
            with requests.get(signed_url, stream=True, timeout=timeout) as response:
                response.raise_for_status()
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
    except Exception:
        try:
            os.remove(temp_path)
        except Exception:
            pass
        raise

    return temp_path