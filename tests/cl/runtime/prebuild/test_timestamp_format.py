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

import re
import pytest
from cl.runtime.prebuild.timestamp_format_util import TimestampFormatUtil
from cl.runtime.primitive.crockford_util import CrockfordUtil

_NEW_FORMAT_RE = re.compile(r"\d{8}-\d{9}-[0-9A-Z]{16}")
"""Regex for the new timestamp format: YYYYMMDD-HHMMSSFFF-CROCKFORD16."""


def _expected_crockford(hex20: str) -> str:
    """Compute the expected Crockford Base32 encoding for a 20-char hex string."""
    return CrockfordUtil.encode(int(hex20, 16), 16)


def test_check_or_fix_text_iso_delimited():
    """Test that ISO-delimited legacy timestamps are detected and converted."""

    text = "ts: 2024-03-13T12:00:00.500Z-abcdef0123456789abcd"

    # Check detects the legacy format
    _, count = TimestampFormatUtil.check_or_fix_text(text, fix=False)
    assert count == 1

    # Fix converts to new format
    fixed, count = TimestampFormatUtil.check_or_fix_text(text, fix=True)
    assert count == 1
    expected = f"ts: 20240313-120000500-{_expected_crockford('abcdef0123456789abcd')}"
    assert fixed == expected


def test_check_or_fix_text_dash_delimited():
    """Test that dash-delimited legacy timestamps are detected and converted."""

    text = "ts: 2024-03-13-12-00-00-500-abcdef0123456789abcd"

    # Check detects the legacy format
    _, count = TimestampFormatUtil.check_or_fix_text(text, fix=False)
    assert count == 1

    # Fix converts to new format
    fixed, count = TimestampFormatUtil.check_or_fix_text(text, fix=True)
    assert count == 1
    expected = f"ts: 20240313-120000500-{_expected_crockford('abcdef0123456789abcd')}"
    assert fixed == expected


def test_check_or_fix_text_both_formats():
    """Test that both legacy formats in the same text are detected and converted."""

    text = (
        "iso: 2024-03-13T12:00:00.500Z-abcdef0123456789abcd\n"
        "dash: 2025-01-15-08-30-45-123-1234567890abcdef1234\n"
    )

    _, count = TimestampFormatUtil.check_or_fix_text(text, fix=False)
    assert count == 2

    fixed, count = TimestampFormatUtil.check_or_fix_text(text, fix=True)
    assert count == 2

    # Both lines should now match the new format
    lines = fixed.strip().split("\n")
    assert _NEW_FORMAT_RE.search(lines[0]) is not None
    assert _NEW_FORMAT_RE.search(lines[1]) is not None


def test_check_or_fix_text_no_legacy():
    """Test that text with no legacy timestamps returns count 0."""

    text = "ts: 20240313-120000500-ABCDEFGHJKMNPQRS\n"
    _, count = TimestampFormatUtil.check_or_fix_text(text, fix=False)
    assert count == 0


def test_check_or_fix(work_dir_fixture):
    """Test check_or_fix_file with stub files containing legacy timestamp formats."""

    iso_file = "invalid_timestamp_iso_delimited.txt"
    dash_file = "invalid_timestamp_dash_delimited.txt"

    # Read original content for restore
    with open(iso_file, "r", encoding="utf-8") as f:
        iso_original = f.read()
    with open(dash_file, "r", encoding="utf-8") as f:
        dash_original = f.read()

    try:
        # Both files should fail validation
        assert not TimestampFormatUtil.check_or_fix_file(iso_file, fix=False)
        assert not TimestampFormatUtil.check_or_fix_file(dash_file, fix=False)

        # Fix both files
        TimestampFormatUtil.check_or_fix_file(iso_file, fix=True)
        TimestampFormatUtil.check_or_fix_file(dash_file, fix=True)

        # Both files should now pass validation
        assert TimestampFormatUtil.check_or_fix_file(iso_file, fix=False)
        assert TimestampFormatUtil.check_or_fix_file(dash_file, fix=False)

        # Verify fixed content has the new format
        with open(iso_file, "r", encoding="utf-8") as f:
            iso_fixed = f.read()
        with open(dash_file, "r", encoding="utf-8") as f:
            dash_fixed = f.read()

        # All timestamps should match the new format
        assert len(_NEW_FORMAT_RE.findall(iso_fixed)) == 2
        assert len(_NEW_FORMAT_RE.findall(dash_fixed)) == 2

        # Both formats with the same date/time/hex should produce the same output
        crockford = _expected_crockford("abcdef0123456789abcd")
        expected_ts = f"20240313-120000500-{crockford}"
        assert expected_ts in iso_fixed
        assert expected_ts in dash_fixed
    finally:
        # Restore original content
        with open(iso_file, "w", encoding="utf-8") as f:
            f.write(iso_original)
        with open(dash_file, "w", encoding="utf-8") as f:
            f.write(dash_original)


if __name__ == "__main__":
    pytest.main([__file__])
