import logging
import os

from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from app.api import (
    allowed_users,
    auth,
    roles,
    user_roles,
    users,
    working_hours,
    bouwplan,
    machines,
    machine_onderhoud,
    tank_transactions,
    ionic,
    vakanties,
)
from app.api.v2 import (
    allowed_users as v2_allowed_users,
    auth as v2_auth,
    working_hours as v2_working_hours,
    users as v2_users,
    vakanties as v2_vakanties,
)
from app.api.v2.admin import (
    working_hours as admin_working_hours,
    roles as admin_roles,
    users as admin_users,
    address as admin_address,
)
from app.db import init_db

log = logging.getLogger("uvicorn")


def create_application() -> FastAPI:
    origin_regex = os.getenv("ORIGIN_REGEX", ".*")
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origin_regex=rf"{origin_regex}",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]

    application = FastAPI(middleware=middleware, root_path="/api")

    # Api voor de nuxt frontend
    app_v1 = FastAPI()
    app_v1.include_router(auth.router, prefix="/auth", tags=["auth"])
    app_v1.include_router(users.router, prefix="/users", tags=["users"])
    app_v1.include_router(
        allowed_users.router, prefix="/allowed_users", tags=["allowed_users"]
    )
    app_v1.include_router(roles.router, prefix="/roles", tags=["roles"])
    app_v1.include_router(user_roles.router, prefix="/user_roles", tags=["user_roles"])
    app_v1.include_router(
        working_hours.router, prefix="/working_hours", tags=["working_hours"]
    )
    app_v1.include_router(bouwplan.router, prefix="/bouwplan", tags=["bouwplan"])
    app_v1.include_router(machines.router, prefix="/machines", tags=["machines"])
    app_v1.include_router(
        machine_onderhoud.router,
        prefix="/machine_maintenance_issues",
        tags=["machine_maintenance_issues"],
    )
    app_v1.include_router(
        tank_transactions.router,
        prefix="/tank_transactions",
        tags=["tank_transactions"],
    )
    app_v1.include_router(vakanties.router, prefix="/vakanties", tags=["vakanties"])
    application.mount("/v1", app_v1)

    # Api voor de quasar frontend
    app_v2 = FastAPI()

    app_v2.include_router(v2_auth.router, prefix="/auth", tags=["auth"])
    app_v2.include_router(
        v2_allowed_users.router, prefix="/allowed_users", tags=["allowed_users"]
    )
    app_v2.include_router(v2_users.router, prefix="/users", tags=["users"])

    app_v2.include_router(
        v2_working_hours.router, prefix="/working_hours", tags=["working_hours"]
    )
    app_v2.include_router(v2_vakanties.router, prefix="/vakanties", tags=["vakanties"])

    # Admin routes
    app_v2.include_router(
        admin_working_hours.router,
        prefix="/admin/working_hours",
        tags=["admin_working_hours"],
    )
    app_v2.include_router(
        admin_roles.router, prefix="/admin/roles", tags=["admin_roles"]
    )
    app_v2.include_router(
        admin_users.router, prefix="/admin/users", tags=["admin_users"]
    )
    app_v2.include_router(
        admin_address.router, prefix="/admin/address", tags=["admin_address"]
    )

    application.mount("/v2", app_v2)
    return application


app = create_application()


@app.on_event("startup")
async def startup_event():
    log.info("Starting up...")
    init_db(app)


@app.on_event("shutdown")
async def shutdown_event():
    log.info("Shutting down...")
