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
from decimal import Decimal
from typing import Any
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.variant.bool_variant import BoolVariant
from cl.runtime.records.variant.data_variant import DataVariant
from cl.runtime.records.variant.date_time_variant import DateTimeVariant
from cl.runtime.records.variant.date_variant import DateVariant
from cl.runtime.records.variant.decimal_variant import DecimalVariant
from cl.runtime.records.variant.float_variant import FloatVariant
from cl.runtime.records.variant.int_variant import IntVariant
from cl.runtime.records.variant.key_variant import KeyVariant
from cl.runtime.records.variant.list_variant import ListVariant
from cl.runtime.records.variant.str_variant import StrVariant
from cl.runtime.records.variant.time_variant import TimeVariant
from cl.runtime.records.variant.variant import Variant


class VariantUtil:
    """Static utility for creating Variant instances from raw values."""

    @staticmethod
    def create(value: Any, metadata: DataclassMixin | None = None) -> Variant:
        """Return a Variant subclass wrapping the given value based on its runtime type.

        Dispatch order:
        1. Variant passthrough (builds if not frozen, metadata ignored)
        2. bool (before int — bool subclasses int)
        3. int
        4. Decimal (before float — more specific numeric type)
        5. float
        6. datetime.datetime (before date — datetime subclasses date)
        7. datetime.date
        8. datetime.time
        9. list | tuple (recursive)
        10. KeyMixin (before DataclassMixin — more specific)
        11. DataclassMixin
        12. Fallback to StrVariant(value=str(value))
        """
        if isinstance(value, Variant):
            return value.build()
        if isinstance(value, bool):
            return BoolVariant(value=value, metadata=metadata).build()
        if isinstance(value, int):
            return IntVariant(value=value, metadata=metadata).build()
        if isinstance(value, Decimal):
            return DecimalVariant(value=value, metadata=metadata).build()
        if isinstance(value, float):
            return FloatVariant(value=value, metadata=metadata).build()
        if isinstance(value, datetime.datetime):
            return DateTimeVariant(value=value, metadata=metadata).build()
        if isinstance(value, datetime.date):
            return DateVariant(value=value, metadata=metadata).build()
        if isinstance(value, datetime.time):
            return TimeVariant(value=value, metadata=metadata).build()
        if isinstance(value, (list, tuple)):
            return ListVariant(value=[VariantUtil.create(v) for v in value], metadata=metadata).build()
        if isinstance(value, KeyMixin):
            return KeyVariant(value=value, metadata=metadata).build()
        if isinstance(value, DataclassMixin):
            return DataVariant(value=value, metadata=metadata).build()
        return StrVariant(value=str(value), metadata=metadata).build()
