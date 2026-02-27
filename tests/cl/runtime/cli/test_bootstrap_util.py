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
from contextlib import contextmanager
from unittest.mock import MagicMock
from unittest.mock import patch
from cl.runtime.cli.bootstrap_util import activate_data_source
from cl.runtime.cli.bootstrap_util import apply_env_config


class TestApplyEnvConfig:
    """Tests for apply_env_config."""

    def test_sets_env_var(self):
        """apply_env_config('win_mongo') sets CL_SETTINGS_ENV."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CL_SETTINGS_ENV", None)
            apply_env_config("win_mongo")
            assert os.environ["CL_SETTINGS_ENV"] == "win_mongo"

    def test_none_is_no_op(self):
        """apply_env_config(None) does not set the env var."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CL_SETTINGS_ENV", None)
            apply_env_config(None)
            assert "CL_SETTINGS_ENV" not in os.environ

    def test_overwrites_existing(self):
        """apply_env_config('new') overwrites a previously set value."""
        with patch.dict(os.environ, {"CL_SETTINGS_ENV": "old"}, clear=False):
            apply_env_config("new")
            assert os.environ["CL_SETTINGS_ENV"] == "new"


class TestActivateDataSource:
    """Tests for activate_data_source context manager."""

    def test_creates_contexts_and_yields(self):
        """activate_data_source activates Env and DataSource and yields active DataSource."""
        mock_ds_instance = MagicMock(name="ds_instance")

        with (
            patch("cl.runtime.cli.bootstrap_util.Env") as mock_env_cls,
            patch("cl.runtime.cli.bootstrap_util.DataSource") as mock_ds_cls,
            patch("cl.runtime.cli.bootstrap_util.activate") as mock_activate,
            patch("cl.runtime.cli.bootstrap_util.active", return_value=mock_ds_instance) as mock_active,
        ):
            # Set up build() return values
            mock_env_obj = MagicMock()
            mock_env_cls.return_value.build.return_value = mock_env_obj
            mock_ds_obj = MagicMock()
            mock_ds_cls.return_value.build.return_value = mock_ds_obj

            # Make activate work as a context manager
            @contextmanager
            def _fake_activate(obj):
                yield obj

            mock_activate.side_effect = _fake_activate

            with activate_data_source() as ds:
                assert ds is mock_ds_instance

            mock_env_cls.return_value.build.assert_called_once()
            mock_ds_cls.return_value.build.assert_called_once()

    def test_is_context_manager(self):
        """activate_data_source can be used as a context manager and exits cleanly."""
        with (
            patch("cl.runtime.cli.bootstrap_util.Env"),
            patch("cl.runtime.cli.bootstrap_util.DataSource"),
            patch("cl.runtime.cli.bootstrap_util.activate") as mock_activate,
            patch("cl.runtime.cli.bootstrap_util.active", return_value=MagicMock()),
        ):

            @contextmanager
            def _fake_activate(obj):
                yield obj

            mock_activate.side_effect = _fake_activate

            # Should not raise
            with activate_data_source() as ds:
                assert ds is not None
