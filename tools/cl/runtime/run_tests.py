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

"""Test runner: shows the currently running test file in-place, prints each failure as soon as it happens
(file as a clickable OSC 8 link, test name indented underneath), writes detailed error info to run_tests.log,
and lists failed tests grouped by file at the end.
"""

import os
import pathlib
import sys

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


REPO_ROOT = os.path.normpath(
    os.environ.get("CL_RUN_TESTS_ROOT")
    or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..")
)


def split_nodeid(nodeid):
    if "::" in nodeid:
        file_part, test_part = nodeid.split("::", 1)
    else:
        file_part, test_part = nodeid, ""
    return file_part, test_part


def link_file(path):
    """Render a path as an OSC 8 hyperlink. path can be absolute or relative to REPO_ROOT."""
    native = path.replace("/", os.sep)
    if os.path.isabs(native):
        abs_path = os.path.normpath(native)
        try:
            display = os.path.relpath(abs_path, REPO_ROOT)
        except ValueError:
            display = abs_path
    else:
        abs_path = os.path.normpath(os.path.join(REPO_ROOT, native))
        display = native
    uri = pathlib.Path(abs_path).as_uri()
    return f"\x1b]8;;{uri}\x1b\\{display}\x1b]8;;\x1b\\"


class ProgressReporter:
    def __init__(self, out, rootpath):
        self.out = out
        self.rootpath = rootpath
        self.current_file = None
        self.last_len = 0
        self.failures = []
        self.errors = []
        self.passed_count = 0
        self.skipped_count = 0
        self._skipped_seen = set()
        self._last_failed_file = None

    def pytest_configure(self, config):
        if hasattr(config, "rootpath"):
            self.rootpath = str(config.rootpath)
        elif hasattr(config, "rootdir"):
            self.rootpath = str(config.rootdir)

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
            return os.path.relpath(abs_path, REPO_ROOT)
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

    def _restore_running(self):
        if self.current_file:
            running = f"  Running: {self.current_file}"
            self.out.write(running)
            self.out.flush()
            self.last_len = len(running)

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
        self._restore_running()

    def pytest_collectstart(self, collector):
        if self.current_file is None:
            self._write_inplace("  Collecting tests...")

    def pytest_runtest_logstart(self, nodeid, location):
        file_part = location[0] if location and location[0] else nodeid.split("::")[0]
        abs_file = self._abs_file(file_part)
        display = self._display(abs_file)
        if display != self.current_file:
            self.current_file = display
            self._last_failed_file = None
            self._write_inplace(f"  Running: {display}")

    def pytest_runtest_logreport(self, report):
        if report.skipped:
            if report.nodeid not in self._skipped_seen:
                self._skipped_seen.add(report.nodeid)
                self.skipped_count += 1
            return

        if report.when == "call":
            if report.passed:
                self.passed_count += 1
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


def run_submodule(name, real_stdout, log_file):
    submodule_dir = os.path.join(REPO_ROOT, name)
    test_dir = os.path.join(submodule_dir, "tests")
    if not os.path.isdir(test_dir):
        real_stdout.write(f"Submodule: {name} (no tests dir)\n")
        real_stdout.flush()
        return [], [], (0, 0, 0)

    real_stdout.write(f"Submodule: {name}\n")
    real_stdout.flush()

    reporter = ProgressReporter(real_stdout, rootpath=submodule_dir)
    saved_stdout, saved_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = log_file, log_file
    try:
        pytest.main([test_dir, "--color=no", "--tb=long"], plugins=[reporter])
    finally:
        sys.stdout, sys.stderr = saved_stdout, saved_stderr

    reporter.finalize()

    succeeded = reporter.passed_count
    failed = len(reporter.failures) + len(reporter.errors)
    skipped = reporter.skipped_count
    real_stdout.write(f"  {format_stats(failed, succeeded, skipped)}\n")
    real_stdout.flush()

    return reporter.failures, reporter.errors, (succeeded, failed, skipped)


def main():
    submodules = ["runtime", "convince", "admin", "resume"]
    log_path = os.path.join(REPO_ROOT, "run_tests.log")

    for sub in submodules:
        path = os.path.join(REPO_ROOT, sub)
        if path not in sys.path:
            sys.path.insert(0, path)

    real_stdout = sys.stdout

    total_succeeded = 0
    total_failed = 0
    total_skipped = 0
    all_failures = []
    all_errors = []

    log_file = open(log_path, "w", encoding="utf-8")
    try:
        for sub in submodules:
            f, e, (s, fa, sk) = run_submodule(sub, real_stdout, log_file)
            all_failures.extend(f)
            all_errors.extend(e)
            total_succeeded += s
            total_failed += fa
            total_skipped += sk
    finally:
        log_file.close()

    print("Project:")
    print(f"  {format_stats(total_failed, total_succeeded, total_skipped)}")

    if all_failures or all_errors:
        if all_failures:
            print("Failed tests:")
            print_grouped(all_failures)
        if all_errors:
            print("Errors:")
            print_grouped(all_errors)
        print(f"See {link_file(log_path)} for detailed error information.")
    else:
        try:
            os.remove(log_path)
        except OSError:
            pass

    sys.exit(0 if not (all_failures or all_errors) else 1)


if __name__ == "__main__":
    main()
