# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from supabase import create_client
# import os

# router = APIRouter()

# class LoginSchema(BaseModel):
#     email: str
#     password: str

# @router.post("/login")
# def login(data: LoginSchema):
#     supabase = create_client(
#         os.getenv("SUPABASE_URL"),
#         os.getenv("SUPABASE_ANON_KEY")
#     )

#     response = supabase.auth.sign_in_with_password({
#         "email": data.email,
#         "password": data.password
#     })

#     if not response.session:
#         raise HTTPException(status_code=401, detail="Credenciais inválidas")

#     return {
#         "access_token": response.session.access_token,
#         "refresh_token": response.session.refresh_token,
#         "token_type": "bearer"
#     }
