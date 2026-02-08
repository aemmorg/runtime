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
from typing import Sequence
from typing_extensions import final
from cl.runtime.project.project_checks import ProjectChecks
from cl.runtime.settings.settings import Settings
from cl.runtime.settings.settings_util import SettingsUtil


@dataclass(slots=True, kw_only=True)
@final
class QaSettings(Settings):
    """QA and unit test settings."""

    qa_db_types: tuple[str, ...] | None = None  # TODO: !! Refactor
    """Database type names for unit testing."""

    qa_dependencies: Sequence[str] | None = None
    """List of dependencies for running the tests (defaults to the standard pytest dependencies)."""

    def __init(self) -> None:
        """Use instead of __init__ in the builder pattern, invoked by the build method in base to derived order."""

        self.qa_db_types = (
            SettingsUtil.to_str_tuple(
                self.qa_db_types,
                field_name="qa_db_types",
                settings_type=type(self),
            )
            if self.qa_db_types is not None
            else tuple()
        )

        # Initialize and validate test dependencies
        if self.qa_dependencies is None:
            self.qa_dependencies = []  # TODO: Add pytest dependencies
        ProjectChecks.guard_requirements(self.qa_dependencies)
