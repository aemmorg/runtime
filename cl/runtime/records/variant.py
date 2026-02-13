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

import datetime
from abc import ABC
from dataclasses import dataclass
from typing import Any
from typing import Self
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin


@dataclass(slots=True, kw_only=True)
class Variant(DataclassMixin, ABC):
    """
    Wrapper for basic scalar values used in UI layers when a schema cannot
    express a single concrete type.

    This class allows different base types to be passed through the UI using
    one stable wrapper type, avoiding the need for unions or `Any` in schemas.

    Intended for data wrapping only.
    """

    metadata: DataclassMixin | None = None
    """Metadata for additional value characteristics."""

    @classmethod
    def create(cls, value: Any, metadata: DataclassMixin | None = None) -> Self:
        """
        Returns a UIValue specialization based on the runtime type of the value.

        Used to wrap a raw value into the appropriate UIValue subclass.
        """

        if isinstance(value, bool):
            return BoolVariant(value=value, metadata=metadata)
        if isinstance(value, int):
            return IntVariant(value=value, metadata=metadata)
        if isinstance(value, float):
            return FloatVariant(value=value, metadata=metadata)
        if isinstance(value, datetime.datetime):
            return DateTimeVariant(value=value, metadata=metadata)
        if isinstance(value, datetime.date):
            return DateVariant(value=value, metadata=metadata)
        if isinstance(value, datetime.time):
            return TimeVariant(value=value, metadata=metadata)

        return StrVariant(value=str(value), metadata=metadata)


@dataclass(slots=True, kw_only=True)
class StrVariant(Variant):
    """
    UIValue specialization for a concrete string type.
    """

    value: str
    "String value of the variant."


@dataclass(slots=True, kw_only=True)
class IntVariant(Variant):
    """
    UIValue specialization for a concrete integer type.
    """

    value: int
    "Integer value of the variant."


@dataclass(slots=True, kw_only=True)
class BoolVariant(Variant):
    """
    UIValue specialization for a concrete bool type.
    """

    value: bool
    "Bool value of the variant."


@dataclass(slots=True, kw_only=True)
class FloatVariant(Variant):
    """
    UIValue specialization for a concrete float type.
    """

    value: float
    "Float value of the variant."


@dataclass(slots=True, kw_only=True)
class DateTimeVariant(Variant):
    """
    UIValue specialization for a concrete datetime type.
    """

    value: datetime.datetime
    "Datetime value of the variant."


@dataclass(slots=True, kw_only=True)
class DateVariant(Variant):
    """
    UIValue specialization for a concrete date type.
    """

    value: datetime.date
    "Date value of the variant."


@dataclass(slots=True, kw_only=True)
class TimeVariant(Variant):
    """
    UIValue specialization for a concrete time type.
    """

    value: datetime.time
    "Time value of the variant."
