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

import logging.config
import os
import sys
import click


def run_command(click_cmd: click.BaseCommand):
    """Bootstrap the runtime and run a Click command as a standalone module.

    Handles --env parsing, sys.path setup, bootstrap import, and logging
    configuration before invoking the Click command. The --env option is
    stripped from sys.argv so it does not conflict with the command's own
    options.

    Usage in any command module::

        if __name__ == "__main__":
            from cl.runtime.cli._standalone import run_command
            run_command(init_db)
    """
    # Parse and strip --env from args
    env_value = None
    raw_args = sys.argv[1:]
    filtered_args = []
    i = 0
    while i < len(raw_args):
        if raw_args[i] == "--env" and i + 1 < len(raw_args):
            env_value = raw_args[i + 1]
            i += 2
        elif raw_args[i].startswith("--env="):
            env_value = raw_args[i].split("=", 1)[1]
            i += 1
        else:
            filtered_args.append(raw_args[i])
            i += 1

    # Ensure bootstrap is loaded
    if "cl.runtime.bootstrap" not in sys.modules:
        import locate

        locate.append_sys_path("../../..")
        import cl.runtime.bootstrap  # noqa: F401 isort: skip

    # Apply env config
    if env_value is not None:
        os.environ["CL_SETTINGS_ENV"] = env_value

    # Configure logging
    from cl.runtime.log.log_config import logging_config  # noqa: E402

    logging.config.dictConfig(logging_config)

    # Run the command with filtered args and proper prog_name
    click_cmd.main(args=filtered_args, prog_name=click_cmd.name, standalone_mode=True)
