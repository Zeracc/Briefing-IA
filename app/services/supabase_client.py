import os
from dotenv import load_dotenv
from supabase import create_client
from supabase.lib.client_options import SyncClientOptions

# Carrega variáveis do .env (sobrescreve env já carregadas)
load_dotenv(override=True)

def _clean_env(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().strip('"').strip("'")

SUPABASE_URL = _clean_env(os.getenv("SUPABASE_URL"))
SUPABASE_KEY = _clean_env(os.getenv("SUPABASE_KEY"))

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL não definido (env ou .env).")

if not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_KEY não definido (env ou .env).")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_supabase_client(access_token: str | None = None):
    if not access_token:
        return supabase
    options = SyncClientOptions(headers={"Authorization": f"Bearer {access_token}"})
    return create_client(SUPABASE_URL, SUPABASE_KEY, options)
