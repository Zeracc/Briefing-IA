import os
from dotenv import load_dotenv
from supabase import create_client
from supabase.lib.client_options import SyncClientOptions
import requests

# Carrega variÃ¡veis do .env (sobrescreve env jÃ¡ carregadas)
load_dotenv(override=True)


def _clean_env(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().strip('"').strip("'")


SUPABASE_URL = _clean_env(os.getenv("SUPABASE_URL"))
SUPABASE_ANON_KEY = _clean_env(os.getenv("SUPABASE_ANON_KEY")) or _clean_env(os.getenv("SUPABASE_KEY"))
SUPABASE_SERVICE_ROLE_KEY = _clean_env(os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
SUPABASE_JWT_SECRET = _clean_env(os.getenv("SUPABASE_JWT_SECRET"))

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL nÃ£o definido (env ou .env).")

if not SUPABASE_ANON_KEY:
    raise RuntimeError("SUPABASE_ANON_KEY/SUPABASE_KEY nÃ£o definido (env ou .env).")

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def get_supabase_client(access_token: str | None = None):
    if not access_token:
        return supabase
    options = SyncClientOptions(headers={"Authorization": f"Bearer {access_token}"})
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY, options)


def insert_as_user(table: str, payload: dict | list, jwt: str, timeout: int = 30) -> dict:
    if not jwt:
        raise ValueError("JWT Ã© obrigatÃ³rio para insert_as_user.")

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {jwt}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    try:
        body = response.json()
    except Exception:
        body = response.text

    return {"ok": response.status_code < 400, "status": response.status_code, "body": body}
