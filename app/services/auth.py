from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.supabase_client import supabase

token_auth = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(token_auth)):
    token = credentials.credentials

    # valida token no Supabase
    user = supabase.auth.get_user(token)

    if not user:
        raise HTTPException(status_code=401, detail="Token inválido")

    return user.user
