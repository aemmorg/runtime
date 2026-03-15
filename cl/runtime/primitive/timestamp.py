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

import datetime as dt
import re
from typing import Any
from typing import TypeGuard
from uuid import UUID
from cl.runtime.exceptions.error_util import ErrorUtil
from cl.runtime.primitive.crockford_util import CrockfordUtil
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.timestamp_uuid import TimestampUuid
from cl.runtime.records.none_checks import NoneChecks
from cl.runtime.records.typename import typename

_ISO_DELIMITED_FORMAT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z-[a-f0-9]{20}$")
"""Regex for the invalid UUIDv7-based timestamp format with ISO-8601 delimiters instead of dash delimiters."""

_LEGACY_TIMESTAMP_FORMAT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d{3}-[a-f0-9]{20}$")
"""Regex for the legacy dash-delimited UUIDv7-based timestamp format yyyy-MM-dd-hh-mm-ss-fff-hex(20)."""


class Timestamp:
    """
    Globally unique UUIDv7 (RFC-9562) timestamp in format YYYYMMDD-HHMMSSFFF-CROCKFORD16.

    Notes:
        Most UUUdv7 algorithms follow RFC-9562 recommendation to use a sequential counter for the first random block.
        This makes the risk of collisions across many simultaneously launched processes unacceptably high.
        The current class uses 74 fully random bits and also guarantees time ordering within each process.
        Across multiple processes, ordering is guaranteed for values generated more than 1ms apart.
    """

    # TODO: Use context vars to prevent a race condition between contexts or threads
    _prev_uuid7 = TimestampUuid.create()
    """The last UUIDv7 created during the previous call within the same context."""

    @classmethod
    def create(cls) -> str:
        """Return a unique timestamp to millisecond precision with 74 fully random bits (no counter).
        The returned values are time-ordered within the same proces among themselves and also
        relative to the tuples returned by create_many(). Across multiple processes,
        ordering is guaranteed for values generated more than 1ms apart.
        """
        # TODO: Multiple contexts or threads are not yet supported
        result = cls.from_uuid7(cls.create_uuid7())
        return result

    @classmethod
    def create_many(cls, count: int) -> tuple[str, ...]:
        """Return sorted UUIDs with v7 layout and 74 fully random bits (no counter).
        The values returned by this method use the same millisecond for the timestamp bits.
        The returned values are time-ordered within the same proces among themselves and also
        relative to the single values returned by create(). Across multiple processes,
        ordering is guaranteed for values generated more than 1ms apart.
        """
        # TODO: Improve performance of create_many by getting many values at the same time and ordering them
        return tuple(cls.from_uuid7(x) for x in cls.create_many_uuid7(count))

    @classmethod
    def create_uuid7(cls) -> UUID:
        """
        Within the same process, thread and context the returned value is greater than any previous values.
        In all other cases, the value is unique and greater than values returned in prior milliseconds.
        """

        # TODO: Multiple contexts or threads are not yet supported

        # Keep getting new uuid7 until it is more than '_prev_uuid7'
        # At worst this will delay execution by one time tick only
        while (result := TimestampUuid.create()) <= cls._prev_uuid7:
            pass

        # Update _prev_uuid7 with the result to ensure strict ordering within the same process thread and context
        cls._prev_uuid7 = result
        return result

    @classmethod
    def create_many_uuid7(cls, count: int) -> tuple[UUID, ...]:
        """
        Within the same process, thread and context returned values are ordered and greater than any previous values.
        In all other cases, the returned values are ordered and greater than values returned in prior milliseconds.
        """
        # TODO: Improve performance of create_many by getting many values at the same time and ordering them
        return tuple(cls.create_uuid7() for _ in range(count))

    @classmethod
    def from_uuid7(cls, value: UUID) -> str:
        """Convert UUIDv7 to the string Timestamp format YYYYMMDD-HHMMSSFFF-CROCKFORD16."""
        # Validate
        cls.validate_uuid7(value)

        # Get the hexadecimal representation of the UUID
        uuid_hex = value.hex

        # Extract the first 12 hex digits representing the timestamp (48 bits = ms since epoch)
        timestamp_ms = int(uuid_hex[:12], 16)

        # Convert milliseconds to a datetime object and format as compact string yyyymmdd-hhmmssfff
        seconds, ms = divmod(timestamp_ms, 1000)
        datetime_obj = dt.datetime.fromtimestamp(seconds, tz=dt.timezone.utc).replace(microsecond=ms * 1000)
        compact_str = DatetimeUtil.to_compact_str(datetime_obj)

        # Encode remaining 20 hex chars (80 bits) as 16 Crockford Base32 chars
        remaining_bits = int(uuid_hex[12:], 16)
        crockford_str = CrockfordUtil.encode(remaining_bits, 16)

        result = f"{compact_str}-{crockford_str}"
        return result

    @classmethod
    def guard_valid(
        cls,
        value: Any,
        *,
        fast: bool = False,
        value_name: str | None = None,
        method_name: str | None = None,
        data_type: type | str | None = None,
        raise_on_fail: bool = True,
    ) -> TypeGuard[str]:
        """Confirm argument is UUIDv7-based timestamp in format YYYYMMDD-HHMMSSFFF-CROCKFORD16."""

        # If fast parameter is true, check length and dash positions for the format YYYYMMDD-HHMMSSFFF-CROCKFORD16
        if fast and isinstance(value, str) and len(value) == 35 and value[8] == "-" and value[18] == "-":
            return True

        # Otherwise rely on conversion to datetime for full validation
        result = cls.to_datetime_or_none(
            value,
            value_name=value_name,
            method_name=method_name,
            data_type=data_type,
            raise_on_fail=raise_on_fail,
        )
        return result is not None

    @classmethod
    def to_datetime(
        cls,
        value: str,
        *,
        value_name: str | None = None,
        method_name: str | None = None,
        data_type: type | str | None = None,
    ) -> dt.datetime:
        """
        Return the UTC datetime component of a UUIDv7 based timestamp in format YYYYMMDD-HHMMSSFFF-CROCKFORD16.

        Args:
            value: UUIDv7 based timestamp in format YYYYMMDD-HHMMSSFFF-CROCKFORD16
            value_name: Variable, field or parameter name for formatting the error message (optional)
            method_name: Method or function name for formatting the error message (optional)
            data_type: Class type or name for formatting the error message (optional)
        """
        # Confirm the value is not None
        assert NoneChecks.guard_not_none(value)

        # Delegate to the method that can also handle None, always raise on fail for this overload
        return cls.to_datetime_or_none(
            value,
            value_name=value_name,
            method_name=method_name,
            data_type=data_type,
        )

    @classmethod
    def to_datetime_or_none(
        cls,
        timestamp: str | None,
        *,
        value_name: str | None = None,
        method_name: str | None = None,
        data_type: type | str | None = None,
        raise_on_fail: bool = True,
    ) -> dt.datetime | None:
        """
        Return the UTC datetime component of a UUIDv7 based timestamp in format YYYYMMDD-HHMMSSFFF-CROCKFORD16,
        or None if the argument is None.

        Args:
            timestamp: UUIDv7 based timestamp in format YYYYMMDD-HHMMSSFFF-CROCKFORD16
            value_name: Variable, field or parameter name for formatting the error message (optional)
            method_name: Method or function name for formatting the error message (optional)
            data_type: Class type or name for formatting the error message (optional)
            raise_on_fail: If the validation fails, return None or raise an error depending on raise_on_fail
        """

        # Handle None first
        if timestamp is None:
            return None

        tokens = timestamp.split("-")
        if (length := len(timestamp)) != 35 or len(tokens) != 3:
            if not raise_on_fail:
                return None
            elif re.match(_ISO_DELIMITED_FORMAT_RE, timestamp):
                # Provide a specific error message for the ISO-delimited format (a frequent error)
                raise ErrorUtil.value_error(
                    timestamp,
                    details=f"""
- It uses legacy format with ISO-8601 delimiters: yyyy-MM-ddThh:mm:ss.fffZ-hex(20)
- Run fix_timestamp_format.py to convert to the new format: YYYYMMDD-HHMMSSFFF-CROCKFORD16
    """,
                    value_name=value_name if value_name is not None else "Timestamp",
                    method_name=method_name,
                    data_type=data_type,
                )
            elif re.match(_LEGACY_TIMESTAMP_FORMAT_RE, timestamp):
                # Provide a specific error message for the legacy dash-delimited format
                raise ErrorUtil.value_error(
                    timestamp,
                    details=f"""
- It uses legacy dash-delimited format: yyyy-MM-dd-hh-mm-ss-fff-hex(20)
- Run fix_timestamp_format.py to convert to the new format: YYYYMMDD-HHMMSSFFF-CROCKFORD16
    """,
                    value_name=value_name if value_name is not None else "Timestamp",
                    method_name=method_name,
                    data_type=data_type,
                )
            else:
                # Provide a generic message for other format errors
                length_str = f"- It has the length of {length} instead of 35\n" if length != 35 else ""
                tokens_str = f"- It has {len(tokens)} dash-delimited tokens instead of 3\n" if len(tokens) != 3 else ""
                raise ErrorUtil.value_error(
                    timestamp,
                    details=f"- Timestamp '{timestamp}' does not conform "
                    f"to the expected format YYYYMMDD-HHMMSSFFF-CROCKFORD16\n"
                    f"{length_str}{tokens_str}",
                    value_name=value_name if value_name is not None else "Timestamp",
                    method_name=method_name,
                    data_type=data_type,
                )

        crockford_str = tokens[2]

        # Parse compact datetime and validate the Crockford suffix
        try:
            result = DatetimeUtil.from_compact_str(f"{tokens[0]}-{tokens[1]}")
            CrockfordUtil.validate(crockford_str, 16)
            # Validate UUIDv7 version bits (0111): first Crockford char encodes 0111x, must be E (14) or F (15)
            if crockford_str[0] not in ("E", "F"):
                raise ValueError(
                    f"UUIDv7 version check failed: first Crockford char must be E or F "
                    f"(version bits 0111), got '{crockford_str[0]}'."
                )
            # Validate UUIDv7 variant bits (10): fourth Crockford char encodes x10xx, bits 3-2 must be 10
            variant_value = CrockfordUtil.decode(crockford_str[3])
            if (variant_value & 0xC) != 0x8:
                raise ValueError(
                    f"UUIDv7 variant check failed: fourth Crockford char must encode "
                    f"variant bits 10 (expected bits 3-2 = 10), got '{crockford_str[3]}'."
                )
        except (ValueError, RuntimeError) as e:
            if raise_on_fail:
                raise ErrorUtil.value_error(
                    timestamp,
                    details=f"""
    - The value does not conform to the expected format YYYYMMDD-HHMMSSFFF-CROCKFORD16
    - It causes the following parsing error:
    {e}
    """,
                    value_name=value_name if value_name is not None else "Timestamp",
                    method_name=method_name,
                    data_type=data_type,
                )
            else:
                return None
        return result

    @classmethod
    def validate(  # TODO: Rename to validate_str, check if it should be merged with guard_valid
        cls,
        timestamp: str,
        *,
        value_name: str | None = None,
        method_name: str | None = None,
        data_type: type | str | None = None,
    ) -> None:
        """
        Validate that the argument is a UUIDv7 based timestamp in format YYYYMMDD-HHMMSSFFF-CROCKFORD16.

        Args:
            timestamp: UUIDv7 based timestamp in format YYYYMMDD-HHMMSSFFF-CROCKFORD16
            value_name: Variable, field or parameter name for formatting the error message (optional)
            method_name: Method or function name for formatting the error message (optional)
            data_type: Class type or name for formatting the error message (optional)
        """
        # Use validation in to_datetime method and discard the result
        cls.to_datetime(
            timestamp,
            value_name=value_name,
            method_name=method_name,
            data_type=data_type,
        )

    @classmethod
    def is_uuid7(cls, value: UUID) -> bool:
        """Return true if the argument is a valid UUIDv7."""

        # Check type using name as UUID class may come from different packages
        if (value_type_name := typename(type(value))) != "UUID":
            raise RuntimeError(f"An object of type '{value_type_name}' was provided while UUIDv7 was expected.")

        # Check that version is UUIDv7
        result = value.version == 7
        return result

    @classmethod
    def validate_uuid7(cls, value: UUID) -> None:
        """Validate that the argument is a valid UUIDv7."""
        if not cls.is_uuid7(value):
            raise RuntimeError(f"UUID v{value.version} was provided while v7 was expected.")
