from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rtls_api.admin import ADMIN_ROUTER
from rtls_api.auth import AUTH_ROUTER, USER_ROUTER
from rtls_api.config import Settings, get_settings
from rtls_api.db import create_session_factory
from rtls_api.session_store import create_refresh_session_store
from rtls_api.spatial_admin import SPATIAL_ADMIN_ROUTER


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = app_settings
        app.state.session_factory = create_session_factory(app_settings)
        app.state.session_store = create_refresh_session_store(
            app_settings.redis_url,
            app_settings.refresh_session_key_prefix,
        )
        yield

    app = FastAPI(
        title="RTLS Analytics Platform API",
        version="0.1.0",
        summary="Identity, RBAC, and audit foundation for the RTLS Analytics Platform.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[app_settings.web_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def read_root() -> dict[str, object]:
        return {
            "product": "RTLS Analytics Platform",
            "environment": app_settings.env,
            "services": {
                "api": f"http://{app_settings.api_host}:{app_settings.api_port}",
                "mqtt-broker": f"{app_settings.mqtt_broker_host}:{app_settings.mqtt_broker_port}",
                "redis": app_settings.redis_url,
                "timescaledb": app_settings.database_url,
                "object-storage": app_settings.object_storage_endpoint,
            },
            "security": {
                "auth": "local-jwt",
                "roles": ["Administrator", "General User"],
            },
        }

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(AUTH_ROUTER)
    app.include_router(USER_ROUTER)
    app.include_router(ADMIN_ROUTER)
    app.include_router(SPATIAL_ADMIN_ROUTER)
    return app


app = create_app()
