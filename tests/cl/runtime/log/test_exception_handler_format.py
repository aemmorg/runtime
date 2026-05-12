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

import traceback
import pytest


def test_format_exception_single_arg():
    """Verify single-arg traceback.format_exception produces the traceback header and the exception line."""

    try:
        raise ValueError("test error message")
    except ValueError as exc:
        formatted = "".join(traceback.format_exception(exc))

    assert "Traceback (most recent call last):" in formatted
    assert "ValueError: test error message" in formatted


def test_exception_handler_log_message():
    """Verify the log message pattern used by handle_exception contains request context and exception line."""

    try:
        raise RuntimeError("something went wrong")
    except RuntimeError as exc:
        log_msg = (
            f"Unhandled exception on POST /api/test: {exc}\n"
            f"{''.join(traceback.format_exception(exc))}"
        )

    assert "Unhandled exception on POST /api/test: something went wrong" in log_msg
    assert "RuntimeError: something went wrong" in log_msg


if __name__ == "__main__":
    pytest.main([__file__])
