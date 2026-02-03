"""Re-exports dos routers para compatibilidade.

Este arquivo expõe tanto os módulos com sufixo `_router` quanto aliases
sem o sufixo (por exemplo, `auth`), para que importações antigas como
`from app.routers import auth` continuem funcionando.
"""
from . import (
    auth_router,
    login_router,
    videos_router,
    projects_router,
    plan_router,
    profile_router,
    recomendations_router,
    transcriptions_router,
)

# aliases sem sufixo para compatibilidade com importações antigas
auth = auth_router
login = login_router
videos = videos_router
projects = projects_router
plan = plan_router
profile = profile_router
recomendations = recomendations_router
transcriptions = transcriptions_router

__all__ = [
    "auth_router",
    "login_router",
    "videos_router",
    "projects_router",
    "plan_router",
    "profile_router",
    "recomendations_router",
    "transcriptions_router",
    "auth",
    "login",
    "videos",
    "projects",
    "plan",
    "profile",
    "recomendations",
    "transcriptions",
]
