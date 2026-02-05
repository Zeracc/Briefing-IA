from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.supabase_client import supabase

token_auth = HTTPBearer(auto_error=False)


def get_access_token(credentials: HTTPAuthorizationCredentials | None = Depends(token_auth)):
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")
    return credentials.credentials


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(token_auth)):
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente")

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


def get_user_id(user) -> str | None:
    if isinstance(user, dict):
        return user.get("id") or user.get("sub")
    return getattr(user, "id", None) or getattr(user, "sub", None)
