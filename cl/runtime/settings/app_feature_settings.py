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

from dataclasses import dataclass
from typing import final
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class AppFeatureSettings(Settings):
    """Backs the `AppFeatures` flags returned by the /settings route.

    Each field maps 1:1 to a field on `AppFeatures`; the wire name is the same minus the
    `app_feature_` prefix. Values can be set via `CL_APP_FEATURE_*` env vars, `.env`, or
    `app_feature_*` keys in `settings.yaml`.
    """

    app_feature_ai_chat: bool | None = None
    """Maps to AppFeatures.ai_chat."""

    app_feature_data_env_support: bool | None = False
    """Maps to AppFeatures.data_env_support."""

    app_feature_dataset_support: bool | None = False
    """Maps to AppFeatures.dataset_support. Used as fallback when no DataSource is in scope."""

    app_feature_db_tools: bool | None = True
    """Maps to AppFeatures.db_tools."""

    app_feature_demo_mode: bool | None = None
    """Maps to AppFeatures.demo_mode."""

    app_feature_internal_apps_support: bool | None = False
    """Maps to AppFeatures.internal_apps_support."""

    app_feature_search_tables: bool | None = None
    """Maps to AppFeatures.search_tables."""

    app_feature_show_user_id: bool | None = True
    """Maps to AppFeatures.show_user_id."""

    app_feature_simplified_ui: bool | None = None
    """Maps to AppFeatures.simplified_ui."""
