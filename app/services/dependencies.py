from fastapi import Header, HTTPException
from supabase import create_client
import os

def get_supabase_user(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")

    token = authorization.replace("Bearer ", "")

    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_ANON_KEY"),
        options={
            "global": {
                "headers": {
                    "Authorization": f"Bearer {token}"
                }
            }
        }
    )
