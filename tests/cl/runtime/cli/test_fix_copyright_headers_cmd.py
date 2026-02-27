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

from unittest.mock import patch
from click.testing import CliRunner
from cl.runtime.cli.fix_copyright_headers_cmd import fix_copyright_headers


class TestFixCopyrightHeadersCmd:
    """Tests for the fix-copyright-headers command."""

    def test_check_only(self, cli_runner: CliRunner):
        """fix-copyright-headers without --fix calls check with fix_header=False."""
        with patch("cl.runtime.prebuild.copyright_util.CopyrightUtil.check_copyright_headers") as mock_check:
            result = cli_runner.invoke(fix_copyright_headers, [])
            assert result.exit_code == 0
            mock_check.assert_called_once_with(fix_header=False, fix_trailing_blank_line=True, verbose=True)

    def test_fix_flag(self, cli_runner: CliRunner):
        """fix-copyright-headers --fix calls check with fix_header=True."""
        with patch("cl.runtime.prebuild.copyright_util.CopyrightUtil.check_copyright_headers") as mock_check:
            result = cli_runner.invoke(fix_copyright_headers, ["--fix"])
            assert result.exit_code == 0
            mock_check.assert_called_once_with(fix_header=True, fix_trailing_blank_line=True, verbose=True)

    def test_error_propagates(self, cli_runner: CliRunner):
        """If the tool raises, the command exits with non-zero."""
        with patch(
            "cl.runtime.prebuild.copyright_util.CopyrightUtil.check_copyright_headers",
            side_effect=RuntimeError("header error"),
        ):
            result = cli_runner.invoke(fix_copyright_headers, [])
            assert result.exit_code != 0

    def test_help(self, cli_runner: CliRunner):
        """fix-copyright-headers --help mentions --fix."""
        result = cli_runner.invoke(fix_copyright_headers, ["--help"])
        assert result.exit_code == 0
        assert "--fix" in result.output
        assert "copyright" in result.output.lower()
