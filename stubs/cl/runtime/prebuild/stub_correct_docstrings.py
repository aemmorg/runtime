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

"""Stub module with correctly formatted docstrings for testing."""


class StubCorrectDocstrings:
    """Stub class with correctly formatted multiline docstrings (summary on the opening quotes line)."""

    def single_line(self) -> None:
        """Single-line docstring."""

    def multi_line_simple(self) -> None:
        """Summary on the first line.

        Additional details on subsequent lines.
        """

    def multi_line_with_args(self) -> str:
        """Summary on the first line with args.

        Args:
            self: Instance reference

        Returns:
            An empty string.

        """
        return ""

    def multi_line_with_notes(self) -> None:
        """Summary on the first line with notes.

        Notes:
            - First note
            - Second note

        """

    @classmethod
    def class_method_multi_line(cls) -> None:
        """Summary on the first line for a classmethod.

        This method does nothing but demonstrates correct docstring format
        for a classmethod with deeper indentation.
        """
