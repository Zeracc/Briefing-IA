from fastapi import APIRouter, Depends, HTTPException
from app.services.auth import get_current_user
from app.services.dependencies import get_supabase_user

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/me")
def get_my_profile(
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_user)
):
    result = (
        supabase
        .table("profiles")
        .select("*")
        .eq("id", user.id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Profile not found")

    return result.data


@router.put("/me")
def update_profile(
    data: dict,
    user=Depends(get_current_user),
    supabase=Depends(get_supabase_user)
):
    update_data = {
        k: v for k, v in {
            "username": data.get("username"),
            "full_name": data.get("full_name")
        }.items() if v is not None
    }

    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")

    response = (
        supabase
        .table("profiles")
        .update(update_data)
        .eq("id", user.id)
        .execute()
    )

    return {"status": "ok", "updated": response.data}

