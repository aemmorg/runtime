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

from contextlib import contextmanager
from unittest.mock import MagicMock
from unittest.mock import patch
import pytest
from click.testing import CliRunner


@pytest.fixture()
def cli_runner():
    """Return a Click CliRunner with separated stderr."""
    return CliRunner()


@pytest.fixture()
def mock_bootstrap():
    """Patch bootstrap side-effects used by the CLI group callback."""
    with (
        patch("cl.runtime.cli.bootstrap_util.apply_env_config") as mock_apply,
        patch("logging.config.dictConfig"),
        patch("cl.runtime.cli.main.logging_config", {"version": 1}, create=True),
    ):
        yield mock_apply


@pytest.fixture()
def mock_activate_data_source():
    """Patch activate_data_source with a no-op context manager yielding a MagicMock."""
    mock_ds = MagicMock(name="DataSource")

    @contextmanager
    def _fake_activate():
        yield mock_ds

    with patch("cl.runtime.cli.bootstrap_util.activate_data_source", _fake_activate):
        yield mock_ds
