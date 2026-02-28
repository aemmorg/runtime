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

"""Stub module with incorrectly formatted docstrings for testing enforced pydocstyle rules."""


class StubWrongDocstrings:
    """Stub class with docstring violations for enforced rules."""

    def over_indented(self) -> None:
        """Summary is fine.

            Over-indented continuation line.
        """
        pass

    def triple_single_quotes(self) -> None:
        '''Single quotes instead of double quotes.'''
        pass

    def surrounding_whitespace(self) -> None:
        """ Summary with leading whitespace. """
        pass

    def empty_docstring(self) -> None:
        """"""
        pass

    @classmethod
    def class_method_over_indented(cls) -> None:
        """Summary is fine.

            Over-indented continuation line for a classmethod.
        """
        pass
