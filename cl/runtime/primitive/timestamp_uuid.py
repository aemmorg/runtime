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
from uuid import UUID

from cl.runtime.primitive.datetime_util import DatetimeUtil


class TimestampUuid:
    """Generate UUID with v7 layout and 74 fully random bits (no counter).

    Notes:
        Most UUUdv7 algorithms follow RFC-9562 recommendation to use a sequential counter for the first random block.
        This makes the risk of collisions across many simultaneously launched processes unacceptably high.
        The current class uses 74 fully random bits and also guarantees time ordering within each process.
        Across multiple processes, ordering is guaranteed for values generated more than 1ms apart.
    """

    @classmethod
    def create(cls) -> UUID:
        """Return a single UUID with v7 layout and 74 fully random bits (no counter).
        The returned values are time-ordered within the same proces among themselves and also
        relative to the tuples returned by create_many(). Across multiple processes,
        ordering is guaranteed for values generated more than 1ms apart.
        """
        now = DatetimeUtil.now()
        ts_ms = int(now.timestamp()) * 1000 + now.microsecond // 1000
        rand = os.urandom(10)

        ba = bytearray(ts_ms.to_bytes(6, "big"))
        ba.extend(rand[:2])
        ba.extend(rand[2:])

        ba[6] = (ba[6] & 0x0F) | 0x70  # version 7
        ba[8] = (ba[8] & 0x3F) | 0x80  # variant 10

        return UUID(bytes=bytes(ba))

    @classmethod
    def create_many(cls, count: int) -> tuple[UUID, ...]:
        """Return sorted timestamps to millisecond precision with 74 fully random bits (no counter).
        The values returned by this method use the same millisecond for the timestamp bits.
        The returned values are time-ordered within the same proces among themselves and also
        relative to the single values returned by create(). Across multiple processes,
        ordering is guaranteed for values generated more than 1ms apart.
        """
        if count < 1:
            raise ValueError("count must be at least 1")

        now = DatetimeUtil.now()
        ts_ms = int(now.timestamp()) * 1000 + now.microsecond // 1000
        prefix = ts_ms.to_bytes(6, "big")

        uuids = []
        for _ in range(count):
            rand = os.urandom(10)
            ba = bytearray(prefix)
            ba.extend(rand[:2])
            ba.extend(rand[2:])
            ba[6] = (ba[6] & 0x0F) | 0x70
            ba[8] = (ba[8] & 0x3F) | 0x80
            uuids.append(UUID(bytes=bytes(ba)))

        uuids.sort()
        return tuple(uuids)

    @classmethod
    def to_iso_str(cls, value: UUID) -> str:
        """Serialize any UUID version to RFC 9562 string with 8-4-4-4-12 formatting after checking its type."""
        if type(value).__name__ == "UUID":
            return str(value)
        else:
            raise RuntimeError(
                f"Class {type(value).__name__} is passed to TimestampUuid.to_str method which expects UUID."
            )

    @classmethod
    def from_iso_str(cls, value: str) -> UUID:
        """Deserialize any UUID version from RFC 9562 string with 8-4-4-4-12 formatting."""
        if isinstance(value, str):
            try:
                # Try to parse as UUID
                result = UUID(value)
            except ValueError:
                raise RuntimeError(f"Cannot parse string '{value}' as UUID.")
        else:
            raise RuntimeError(
                f"Class {type(value).__name__} is passed to TimestampUuid.from_str method which expects str."
            )
        return result
