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

import base32_crockford


class CrockfordUtil:
    """Crockford Base32 encoding and decoding using the base32-crockford package."""

    @classmethod
    def encode(cls, value: int, length: int) -> str:
        """Encode a non-negative integer to a fixed-length uppercase Crockford Base32 string."""
        if value < 0:
            raise ValueError(f"Cannot Crockford-encode negative value {value}.")
        result = base32_crockford.encode(value)
        if len(result) > length:
            raise ValueError(f"Value too large to encode in {length} Crockford Base32 characters.")
        return result.zfill(length)

    @classmethod
    def decode(cls, value: str) -> int:
        """Decode a Crockford Base32 string to a non-negative integer."""
        return base32_crockford.decode(value)

    @classmethod
    def validate(cls, value: str, length: int) -> None:
        """Validate that the string is a valid Crockford Base32 encoding of the given length."""
        if len(value) != length:
            raise ValueError(f"Crockford Base32 string '{value}' has length {len(value)}, expected {length}.")
        for ch in value:
            try:
                base32_crockford.decode(ch)
            except ValueError:
                raise ValueError(f"Invalid Crockford Base32 character '{ch}' in '{value}'.")
