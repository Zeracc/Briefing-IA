from fastapi import APIRouter, Depends, HTTPException
from app.services.supabase_client import get_supabase_client
from app.services.auth import get_current_user, get_access_token, get_user_id

router = APIRouter(prefix="/profile")


@router.get("/me")
def get_my_profile(user=Depends(get_current_user), token=Depends(get_access_token)):
    client = get_supabase_client(token)
    user_id = get_user_id(user)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalido")
    response = (
        client.table("profiles")
        .select("*")
        .eq("id", user_id)
        .single()
        .execute()
    )
    return response.data


@router.put("/")
def update_profile(data: dict, user=Depends(get_current_user), token=Depends(get_access_token)):
    client = get_supabase_client(token)
    user_id = get_user_id(user)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalido")
    update_data = {
        "username": data.get("username"),
        "full_name": data.get("full_name")
    }

    response = (
        client.table("profiles")
        .update(update_data)
        .eq("id", user_id)
        .execute()
    )

    return {"status": "ok", "updated": response.data}
