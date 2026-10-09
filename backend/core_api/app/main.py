from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.routers.health import router as health_router
from app.modules.calls.router import router as calls_router
from app.modules.dashboard.router import router as dashboard_router
from fastapi.responses import JSONResponse
from app.core.exceptions import AppError


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    #Application lifespan manager. DB schema managed by Alembic migrations; no create_all at startup."""
    # init_db() removed: schema managed by Alembic (production). For dev, run `alembic upgrade head`.
    yield

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        setup_logging=settings.LOG_LEVEL,
        lifespan=lifespan,

    )
    @app.exception_handler(AppError)
    async def app_error_handler(request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "code": exc.code,
                "message": str(exc),
            },
        )


    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(calls_router, prefix=settings.API_V1_PREFIX,)
    app.include_router(dashboard_router, prefix=settings.API_V1_PREFIX,)

    return app


app = create_app()