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

from pydantic import BaseModel
from pydantic import ConfigDict
from cl.runtime.primitive.case_util import CaseUtil


class AppFeatures(BaseModel):
    """Optional feature flags returned by the /settings route."""

    model_config = ConfigDict(alias_generator=CaseUtil.snake_to_pascal_case, populate_by_name=True)

    ai_chat: bool | None = None
    """
    Enables or disables the AI Chat feature.
    When True, users can engage in context-aware dialogue with AI Chatbot based on UI focus.
    """

    dataset_support: bool | None = False
    """
    Enables dataset integration and manipulation features.
    When True, the UI will display dataset selection controls
    otherwise, all dataset-related features are hidden.
    Dynamically resolved from the active data source in get_response().
    """

    db_tools: bool | None = True
    """Enables database tools (Export Database, Import Database) in the UI."""

    demo_mode: bool | None = None
    """
    Activates demo mode for presentations or testing.
    May limit error reporting functionality.
    """

    envs_support: bool | None = True
    """Enables environment management features in the UI."""
