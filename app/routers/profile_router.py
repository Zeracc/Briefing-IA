from fastapi import APIRouter, Depends
from app.services.supabase_client import supabase
from app.services.auth import get_current_user

router = APIRouter(prefix="/profile")

@router.get("/me")
def get_my_profile(user=Depends(get_current_user)):
    response = (
        supabase.table("profiles")
        .select("*")
        .eq("id", user.id)
        .single()
        .execute()
    )
    return response.data

@router.put("/")
def update_profile(data: dict, user=Depends(get_current_user)):
    update_data = {
        "username": data.get("username"),
        "full_name": data.get("full_name")
    }

    response = (
        supabase.table("profiles")
        .update(update_data)
        .eq("id", user.id)
        .execute()
    )

    return {"status": "ok", "updated": response.data}
