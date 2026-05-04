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

"""Test runner: distributes tests across CPU cores via pytest-xdist, shows live pass/fail/skip counts in-place,
prints each failure as soon as it happens (file as a clickable OSC 8 link, test name indented underneath),
writes detailed error info to run_tests.log, and lists failed tests grouped by file at the end.
"""

import importlib.util
import os
import pathlib
import sys

if importlib.util.find_spec("xdist") is None:
    sys.stderr.write(
        "ERROR: pytest-xdist is required by run_tests.py for parallel execution but is not installed.\n"
        "Install it with:  pip install pytest-xdist\n"
    )
    sys.exit(2)

import pytest


if sys.platform == "win32":
    try:
        import ctypes
        _kernel32 = ctypes.windll.kernel32
        _handle = _kernel32.GetStdHandle(-11)
        _mode = ctypes.c_ulong()
        if _kernel32.GetConsoleMode(_handle, ctypes.byref(_mode)):
            _kernel32.SetConsoleMode(_handle, _mode.value | 0x0004)
    except Exception:
        pass


# Bootstrap sys.path so cl.runtime.* is importable, then resolve the project root via ProjectLayout.
# This file lives at <repo>/runtime/tools/cl/runtime/run_tests.py, so parents[3] is <repo>/runtime,
# which is the runtime package's source root (the entry that needs to be on PYTHONPATH).
_RUNTIME_SRC = str(pathlib.Path(__file__).resolve().parents[3])
if _RUNTIME_SRC not in sys.path:
    sys.path.insert(0, _RUNTIME_SRC)

from cl.runtime.project.project_layout import ProjectLayout  # noqa: E402

PROJECT_ROOT = ProjectLayout.get_project_root()


def split_nodeid(nodeid):
    if "::" in nodeid:
        file_part, test_part = nodeid.split("::", 1)
    else:
        file_part, test_part = nodeid, ""
    return file_part, test_part


def link_file(path):
    """Render a path as an OSC 8 hyperlink. path can be absolute or relative to PROJECT_ROOT."""
    native = path.replace("/", os.sep)
    if os.path.isabs(native):
        abs_path = os.path.normpath(native)
        try:
            display = os.path.relpath(abs_path, PROJECT_ROOT)
        except ValueError:
            display = abs_path
    else:
        abs_path = os.path.normpath(os.path.join(PROJECT_ROOT, native))
        display = native
    uri = pathlib.Path(abs_path).as_uri()
    return f"\x1b]8;;{uri}\x1b\\{display}\x1b]8;;\x1b\\"


class ProgressReporter:
    def __init__(self, out, rootpath):
        self.out = out
        self.rootpath = rootpath
        self.last_len = 0
        self.failures = []
        self.errors = []
        self.passed_count = 0
        self.skipped_count = 0
        self.total_count = None
        self.worker_count = None
        self._skipped_seen = set()
        self._last_failed_file = None

    def pytest_configure(self, config):
        if hasattr(config, "rootpath"):
            self.rootpath = str(config.rootpath)
        elif hasattr(config, "rootdir"):
            self.rootpath = str(config.rootdir)

    def pytest_collection_modifyitems(self, config, items):
        self.total_count = len(items)
        self._update_progress()

    def pytest_xdist_setupnodes(self, config, specs):
        self.worker_count = len(specs)
        self._update_progress()

    def pytest_xdist_node_collection_finished(self, node, ids):
        if self.total_count is None:
            self.total_count = len(ids)
            self._update_progress()

    def _abs_file(self, file_part):
        native = file_part.replace("/", os.sep)
        if os.path.isabs(native):
            return os.path.normpath(native)
        return os.path.normpath(os.path.join(self.rootpath, native))

    def _resolve(self, nodeid):
        file_part, test_part = split_nodeid(nodeid)
        abs_file = self._abs_file(file_part)
        if test_part:
            return f"{abs_file}::{test_part}"
        return abs_file

    def _display(self, abs_path):
        try:
            return os.path.relpath(abs_path, PROJECT_ROOT)
        except ValueError:
            return abs_path

    def _clear_line(self):
        if self.last_len:
            self.out.write("\r" + " " * self.last_len + "\r")
            self.out.flush()
            self.last_len = 0

    def _write_inplace(self, msg):
        self._clear_line()
        self.out.write(msg)
        self.out.flush()
        self.last_len = len(msg)

    def _progress_msg(self):
        done = self.passed_count + self.skipped_count + len(self.failures) + len(self.errors)
        parts = [f"passed={self.passed_count}"]
        if self.failures:
            parts.append(f"failed={len(self.failures)}")
        if self.errors:
            parts.append(f"errors={len(self.errors)}")
        if self.skipped_count:
            parts.append(f"skipped={self.skipped_count}")
        if self.total_count:
            head = f"  Progress: {done}/{self.total_count}"
        else:
            head = f"  Progress: {done}"
        if self.worker_count:
            head += f" [{self.worker_count} workers]"
        return f"{head} ({', '.join(parts)})"

    def _update_progress(self):
        self._write_inplace(self._progress_msg())

    def _print_failure(self, resolved_nodeid, kind):
        file_part, test_part = split_nodeid(resolved_nodeid)
        file_display = self._display(file_part)

        self._clear_line()

        if file_display != self._last_failed_file:
            self._last_failed_file = file_display
            self.out.write(f"  {kind}: {link_file(file_part)}\n")

        if test_part:
            self.out.write(f"    {test_part}\n")

        self.out.flush()
        self._update_progress()

    def pytest_collectstart(self, collector):
        if self.total_count is None and self.last_len == 0:
            self._write_inplace("  Collecting tests...")

    def pytest_runtest_logreport(self, report):
        if report.skipped:
            if report.nodeid not in self._skipped_seen:
                self._skipped_seen.add(report.nodeid)
                self.skipped_count += 1
                self._update_progress()
            return

        if report.when == "call":
            if report.passed:
                self.passed_count += 1
                self._update_progress()
            elif report.failed:
                resolved = self._resolve(report.nodeid)
                if resolved not in self.failures:
                    self.failures.append(resolved)
                    self._print_failure(resolved, "Failed")
        elif report.when in ("setup", "teardown"):
            if report.failed:
                resolved = self._resolve(report.nodeid)
                if resolved not in self.errors and resolved not in self.failures:
                    self.errors.append(resolved)
                    self._print_failure(resolved, "Error")

    def pytest_collectreport(self, report):
        if report.failed and report.nodeid:
            resolved = self._resolve(report.nodeid)
            if resolved not in self.errors:
                self.errors.append(resolved)
                self._print_failure(resolved, "Error")

    def finalize(self):
        self._clear_line()


def format_stats(failed, succeeded, skipped):
    parts = []
    if failed > 0:
        parts.append(f"Failed: {failed}")
    parts.append(f"Succeeded: {succeeded}")
    if skipped > 0:
        parts.append(f"Skipped: {skipped}")
    return ", ".join(parts)


def print_grouped(nodeids):
    by_file = {}
    order = []
    for nodeid in nodeids:
        file_part, test_part = split_nodeid(nodeid)
        if file_part not in by_file:
            by_file[file_part] = []
            order.append(file_part)
        if test_part:
            by_file[file_part].append(test_part)
    for file_part in order:
        print(f"  {link_file(file_part)}")
        for test in by_file[file_part]:
            print(f"    {test}")


def main():
    all_submodules = ["runtime", "convince", "admin", "resume"]

    # Optional positional args: subset of submodule names to run (default: all).
    requested = sys.argv[1:]
    if requested:
        unknown = [s for s in requested if s not in all_submodules]
        if unknown:
            sys.stderr.write(
                f"ERROR: unknown submodule(s): {', '.join(unknown)}. "
                f"Known: {', '.join(all_submodules)}\n"
            )
            sys.exit(2)
        submodules = requested
    else:
        submodules = all_submodules

    # Log file is written to the current working directory. Wrapper .cmd scripts are responsible
    # for setting CWD to where they want the log to land (typically next to the .cmd file).
    log_path = os.path.join(os.getcwd(), "run_tests.log")

    # Build the list of paths needed by both the controller process and xdist worker subprocesses.
    # PROJECT_ROOT is required so cross-submodule imports like `from resume.cl.resume...` resolve when
    # one submodule's source references another by its top-level package name. All submodule paths
    # are added regardless of which subset is being run, since cross-submodule imports still occur.
    extra_paths = [PROJECT_ROOT] + [os.path.join(PROJECT_ROOT, sub) for sub in all_submodules]

    # In-process sys.path for the controller (also affects serial pytest runs without xdist).
    for path in extra_paths:
        if path not in sys.path:
            sys.path.insert(0, path)

    # PYTHONPATH for xdist worker subprocesses, which do not inherit in-process sys.path edits.
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    pythonpath_parts = [p for p in extra_paths if p not in existing_pythonpath.split(os.pathsep)]
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    os.environ["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)

    test_dirs = []
    for sub in submodules:
        test_dir = os.path.join(PROJECT_ROOT, sub, "tests")
        if os.path.isdir(test_dir):
            test_dirs.append(test_dir)

    real_stdout = sys.stdout
    reporter = ProgressReporter(real_stdout, rootpath=PROJECT_ROOT)

    log_file = open(log_path, "w", encoding="utf-8")
    saved_stdout, saved_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = log_file, log_file
    try:
        pytest.main(
            [*test_dirs, "-n", "auto", "--dist=loadfile", "--rootdir", PROJECT_ROOT, "--color=no", "--tb=long"],
            plugins=[reporter],
        )
    finally:
        sys.stdout, sys.stderr = saved_stdout, saved_stderr
        log_file.close()

    reporter.finalize()

    succeeded = reporter.passed_count
    failed = len(reporter.failures) + len(reporter.errors)
    skipped = reporter.skipped_count
    print("Project:")
    print(f"  {format_stats(failed, succeeded, skipped)}")

    if reporter.failures or reporter.errors:
        if reporter.failures:
            print("Failed tests:")
            print_grouped(reporter.failures)
        if reporter.errors:
            print("Errors:")
            print_grouped(reporter.errors)
        print(f"See {link_file(log_path)} for detailed error information.")
        sys.exit(1)
    else:
        try:
            os.remove(log_path)
        except OSError:
            pass
        sys.exit(0)


if __name__ == "__main__":
    main()
