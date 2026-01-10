from fastapi import Depends, HTTPException, status
from app.services.auth import get_current_user
from app.services.dependencies import get_supabase_user

def require_plan(allowed: list[str]):
    def checker(
        user=Depends(get_current_user),
        supabase=Depends(get_supabase_user)
    ):
        profile = (
            supabase
            .table("profiles")
            .select("plan")
            .eq("id", user.id)
            .single()
            .execute()
            .data
        )

        if not profile or profile["plan"] not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your plan does not allow this action"
            )

        return profile

    return checker
