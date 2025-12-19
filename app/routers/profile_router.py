from fastapi import APIRouter, Depends
from app.services.auth import get_current_user
from app.services.dependencies import get_supabase_user_user

router = APIRouter(prefix="/profile")

@router.get("/me")
def get_my_profile(
    supabase = Depends(get_supabase_user_user)
):
    return (
        supabase
        .table("profiles")
        .select("*")
        .single()
        .execute()
        .data
    )

@router.put("/")
def update_profile(
    data: dict, 
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_user_user)
):
    update_data = {
        k: v for k, v in {
            "username": data.get("username"),
            "full_name": data.get("full_name")
        }.items() if v is not None
    }

    response = (
        supabase
        .table("profiles")
        .update(update_data)
        .eq("id", user.id)
        .execute()
    )

    return {"status": "ok", "updated": response.data}