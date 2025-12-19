import os
from supabase import create_client
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_supabase_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY"),
        options={
            "global": {
                "headers": {
                    "Authorization": f"Bearer {credentials.credentials}"
                }
            }
        }
    )
