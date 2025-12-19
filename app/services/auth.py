from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.dependencies import get_supabase_user

token_auth = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(token_auth),
    supabase = Depends(get_supabase_user)
):
    token = credentials.credentials

    user_response = supabase.auth.get_user(token)

    if not user_response or not user_response.user:
        raise HTTPException(status_code=401, detail="Token inválido")

    return user_response.user
