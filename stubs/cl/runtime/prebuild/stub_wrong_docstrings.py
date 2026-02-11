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


class StubWrongDocstrings:
    """
    Stub class with incorrectly formatted multiline docstrings (opening quotes on a separate line).
    """

    def multi_line_simple(self) -> None:
        """
        Summary on a separate line from the opening quotes.

        Additional details on subsequent lines.
        """
        pass

    def multi_line_with_args(self) -> str:
        """
        Summary on a separate line with args.

        Args:
            self: Instance reference

        Returns:
            An empty string.
        """
        return ""

    def multi_line_with_notes(self) -> None:
        """
        Summary on a separate line with notes.

        Notes:
            - First note
            - Second note
        """
        pass

    @classmethod
    def class_method_multi_line(cls) -> None:
        """
        Summary on a separate line for a classmethod.

        This method does nothing but demonstrates incorrect docstring format
        for a classmethod with deeper indentation.
        """
        pass
