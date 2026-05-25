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

from cl.runtime.contexts.context_manager import active
from cl.runtime.records.for_pydantic.pydantic_mixin import PydanticMixin
from cl.runtime.server.env import Env
from cl.runtime.services.app.internal_app_descriptor import InternalAppDescriptor
from cl.runtime.services.app.internal_apps import InternalApps


class AppService(PydanticMixin):
    """Service class for internal-app management actions.

    Contract-stub implementation: the active Env is reported as the single available internal app.
    Persistence of multiple apps and switching the active app are not supported on this build.
    """

    @classmethod
    def run_internal_apps(cls) -> InternalApps:
        """Return the current internal-app configuration synthesized from the active Env."""
        env = active(Env)
        descriptor = InternalAppDescriptor(
            app_name=env.env_id,
            app_kind=env.env_kind.name,
            parent=None,
            url=None,
            description="Current internal app",
        )
        return InternalApps(
            active_app_name=env.env_id,
            apps=[descriptor],
        )

    @classmethod
    def run_set_active_internal_app(cls, app_name: str) -> None:
        """Validate that `app_name` matches the only synthesized app; raise otherwise."""
        env_id = active(Env).env_id
        if app_name != env_id:
            raise RuntimeError(
                f"Internal app '{app_name}' not found. Available internal apps: {env_id}."
            )
