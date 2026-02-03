from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.supabase_client import supabase

token_auth = HTTPBearer()


def get_access_token(credentials: HTTPAuthorizationCredentials = Depends(token_auth)):
    return credentials.credentials


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(token_auth)):
    token = credentials.credentials

    # valida token no Supabase
    try:
        user_resp = supabase.auth.get_user(token)
    except Exception as exc:
        # evita 500 sem CORS quando o Supabase esta indisponivel
        print("Supabase auth.get_user error:", repr(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth service unavailable",
        )

    # suporta diferentes formatos de retorno do client
    error = None
    user = None
    if isinstance(user_resp, dict):
        error = user_resp.get("error") or (user_resp.get("data") or {}).get("error")
        user = user_resp.get("user") or (user_resp.get("data") or {}).get("user")
    else:
        error = getattr(user_resp, "error", None)
        user = getattr(user_resp, "user", None)

    if error or not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido")

    return user
