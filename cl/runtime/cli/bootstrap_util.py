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

import os
from contextlib import contextmanager
from typing import Iterator
from cl.runtime.contexts.context_manager import activate
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.server.env import Env


def apply_env_config(env: str | None) -> None:
    """Set CL_SETTINGS_ENV environment variable if --env option is provided."""
    if env is not None:
        os.environ["CL_SETTINGS_ENV"] = env


@contextmanager
def activate_data_source() -> Iterator[DataSource]:
    """Context manager that activates Env and DataSource contexts."""
    with activate(Env().build()), activate(DataSource().build()):
        yield active(DataSource)
