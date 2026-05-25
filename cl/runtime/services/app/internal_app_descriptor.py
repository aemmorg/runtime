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

from cl.runtime.records.for_pydantic.pydantic_mixin import PydanticMixin


class InternalAppDescriptor(PydanticMixin):
    """Metadata describing an internal app."""

    app_name: str
    """Name of the internal app."""

    app_kind: str | None = None
    """Internal app kind that determines the policies for data protection and retention."""

    parent: str | None = None
    """Name of the parent internal app."""

    url: str | None = None
    """URL of the internal app backend API. None if matches current backend URL."""

    description: str | None = None
    """Description of the internal app backend API."""
