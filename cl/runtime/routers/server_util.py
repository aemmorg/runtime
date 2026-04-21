# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from fastapi import Depends
from fastapi import FastAPI
from cl.runtime.routers.app import app_router
from cl.runtime.routers.auth import auth_router
from cl.runtime.routers.health import health_router
from cl.runtime.routers.schema import schema_router
from cl.runtime.routers.settings import settings_router
from cl.runtime.routers.sse import sse_router
from cl.runtime.routers.storage import storage_router
from cl.runtime.routers.task import task_router
from cl.runtime.routers.ui_events import ui_events_router
from cl.runtime.routers.workers.workers_router import router as workers_router
from cl.runtime.server.auth_dependency import activate_auth_context


class ServerUtil:
    """Configures FastAPI server app for uvicorn or test client."""

    @classmethod
    def normalize_api_prefix(cls, api_prefix: str | None) -> str:
        """Normalize api_prefix to prevent malformed routes.

        Defensive normalization ensures correct routes even if the raw
        config value leaks through unprocessed.

        Args:
            api_prefix: Raw api_prefix value from settings

        Returns:
            Normalized prefix (empty string if None, "/", or invalid)
        """
        if not api_prefix:
            return ""
        # Normalize consecutive slashes to single slash (e.g., /api//v1 -> /api/v1)
        api_prefix = re.sub(r"/+", "/", api_prefix)
        # Strip trailing slashes to prevent double slashes (e.g., /api/v1//auth)
        api_prefix = api_prefix.rstrip("/")
        # Treat "/" (after stripping) as no prefix
        if not api_prefix:
            return ""
        # Ensure prefix starts with "/" - if not, prefix with "/"
        if not api_prefix.startswith("/"):
            api_prefix = f"/{api_prefix}"
        return api_prefix

    @classmethod
    def include_routers(cls, server_app: FastAPI) -> None:
        """Register all API routers with the FastAPI application.

        Args:
            server_app: FastAPI application instance to register routers with
        """

        server_app.include_router(app_router.router, tags=["App"])
        server_app.include_router(health_router.router, tags=["Health Check"])
        server_app.include_router(settings_router.router, tags=["Application Settings"])
        server_app.include_router(auth_router.router, prefix="/auth", tags=["Authorization"])

        # Routers with Auth dependency
        server_app.include_router(
            sse_router.router, prefix="/sse", tags=["SSE"], dependencies=[Depends(activate_auth_context)]
        )
        server_app.include_router(
            schema_router.router,
            prefix="/schema",
            tags=["Schema"],
            dependencies=[Depends(activate_auth_context)],
        )
        server_app.include_router(
            storage_router.router,
            prefix="/storage",
            tags=["Storage"],
            dependencies=[Depends(activate_auth_context)],
        )
        server_app.include_router(
            task_router.router,
            prefix="/task",
            tags=["Task"],
            dependencies=[Depends(activate_auth_context)],
        )
        server_app.include_router(
            ui_events_router.router,
            prefix="/ui",
            tags=["UI Events"],
            dependencies=[Depends(activate_auth_context)],
        )
        server_app.include_router(
            workers_router,
            prefix="/workers",
            tags=["Workers"],
            dependencies=[Depends(activate_auth_context)],
        )
