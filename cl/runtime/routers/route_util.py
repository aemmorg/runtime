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

from fastapi import HTTPException


class RouteUtil:
    """Utilities for FastAPI route parameter resolution."""

    @staticmethod
    def resolve(query_value: str | None, body_value: str | None, field_name: str) -> str:
        """Return query param if provided, else body param. Raise 422 if both are None."""
        result = query_value if query_value is not None else body_value
        if result is None:
            raise HTTPException(
                status_code=422,
                detail=f"'{field_name}' must be provided as query param or in request body.",
            )
        return result
