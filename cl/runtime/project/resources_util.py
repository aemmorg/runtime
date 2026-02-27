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

import posixpath
from cl.runtime.project.project_util import ProjectUtil
from cl.runtime.settings.dynaconf_loader import DynaconfLoader


class ResourcesUtil:
    """Helper methods for managing resources that persist between runs."""

    @classmethod
    def get_resources_root(cls) -> str:
        """Contains resources that persist across multiple code runs, specific to Dynaconf environment."""
        project_root = ProjectUtil.get_project_root()
        settings_env = DynaconfLoader.instance().get_settings_env()
        return posixpath.normpath(posixpath.join(project_root, "resources", settings_env))

    @classmethod
    def get_bootstrap_root(cls) -> str:
        """Contains resources used for type system initialization."""
        resources_root = cls.get_resources_root()
        return posixpath.normpath(posixpath.join(resources_root, "bootstrap"))
