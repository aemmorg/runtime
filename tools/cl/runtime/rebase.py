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

"""Fetch and rebase (or fast-forward) every submodule and the root repo onto its origin branch."""

import configparser
import os
import pathlib
import subprocess
import sys

_RUNTIME_SRC = str(pathlib.Path(__file__).resolve().parents[3])
if _RUNTIME_SRC not in sys.path:
    sys.path.insert(0, _RUNTIME_SRC)

from cl.runtime.project.project_layout import ProjectLayout  # noqa: E402

PROJECT_ROOT = ProjectLayout.get_project_root()


def run_git(args, cwd):
    """Run a git command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        ["git"] + args, cwd=cwd, capture_output=True, text=True, encoding="utf-8"
    )
    return result.returncode, result.stdout.rstrip(), result.stderr.strip()


def get_submodules():
    """Parse .gitmodules and return a list of submodule paths."""
    gitmodules_path = os.path.join(PROJECT_ROOT, ".gitmodules")
    if not os.path.isfile(gitmodules_path):
        return []
    parser = configparser.ConfigParser()
    parser.read(gitmodules_path)
    paths = []
    for section in parser.sections():
        if section.startswith("submodule "):
            path = parser.get(section, "path", fallback=None)
            if path:
                paths.append(path)
    return paths


def get_current_branch(repo_path):
    """Return the current branch name, or None if HEAD is detached."""
    rc, out, _ = run_git(["symbolic-ref", "--short", "HEAD"], cwd=repo_path)
    if rc != 0:
        return None
    return out


def has_uncommitted_changes(repo_path, is_root=False):
    """Check for uncommitted changes. For root repo, ignore submodule pointer changes."""
    rc, out, _ = run_git(["status", "--porcelain"], cwd=repo_path)
    if rc != 0 or not out:
        return False, []

    lines = out.splitlines()
    if is_root:
        submodule_dirs = set(get_submodules())
        filtered = [line for line in lines if line[3:].strip().rstrip("/") not in submodule_dirs]
        return bool(filtered), filtered
    return bool(lines), lines


def rebase_repo(repo_path, label):
    """Fetch origin, then fast-forward or rebase onto origin/<branch>. Returns True on success."""
    branch = get_current_branch(repo_path)
    if branch is None:
        print(f"  {label}: skipped (detached HEAD)")
        return False

    print(f"  {label} ({branch}): fetching...")
    rc, _, err = run_git(["fetch", "origin"], cwd=repo_path)
    if rc != 0:
        print(f"  {label} ({branch}): fetch failed - {err}")
        return False

    rc, local_sha, _ = run_git(["rev-parse", "HEAD"], cwd=repo_path)
    if rc != 0:
        print(f"  {label} ({branch}): cannot resolve HEAD")
        return False

    rc, remote_sha, _ = run_git(["rev-parse", f"origin/{branch}"], cwd=repo_path)
    if rc != 0:
        print(f"  {label} ({branch}): origin/{branch} not found")
        return False

    rc, merge_base, _ = run_git(["merge-base", local_sha, remote_sha], cwd=repo_path)
    if rc != 0:
        print(f"  {label} ({branch}): cannot compute merge base")
        return False

    if local_sha == remote_sha:
        print(f"  {label} ({branch}): already up to date")
        return True

    if local_sha == merge_base:
        print(f"  {label} ({branch}): fast-forwarding...")
        rc, _, err = run_git(["merge", "--ff-only", f"origin/{branch}"], cwd=repo_path)
        if rc != 0:
            print(f"  {label} ({branch}): fast-forward failed - {err}")
            return False
        print(f"  {label} ({branch}): fast-forwarded")
        return True

    print(f"  {label} ({branch}): rebasing onto origin/{branch}...")
    rc, _, err = run_git(["rebase", f"origin/{branch}"], cwd=repo_path)
    if rc != 0:
        run_git(["rebase", "--abort"], cwd=repo_path)
        print(f"  {label} ({branch}): rebase failed (aborted) - {err}")
        return False
    print(f"  {label} ({branch}): rebased")
    return True


def main():
    submodules = get_submodules()
    if not submodules:
        print("No submodules found in .gitmodules")
        sys.exit(2)

    # Initialize any uninitialized submodules
    print("Initializing submodules...")
    rc, _, err = run_git(["submodule", "update", "--init"], cwd=PROJECT_ROOT)
    if rc != 0:
        print(f"  submodule init failed - {err}")
        sys.exit(2)

    # Check for uncommitted changes in all repos before doing anything
    dirty = []
    dirty_flag, dirty_files = has_uncommitted_changes(PROJECT_ROOT, is_root=True)
    if dirty_flag:
        dirty.append(("root", dirty_files))

    for sub in submodules:
        sub_path = os.path.join(PROJECT_ROOT, sub)
        if not os.path.isdir(os.path.join(sub_path, ".git")) and not os.path.isfile(
            os.path.join(sub_path, ".git")
        ):
            continue
        flag, files = has_uncommitted_changes(sub_path)
        if flag:
            dirty.append((sub, files))

    if dirty:
        print("ERROR: uncommitted changes detected, commit or stash before rebasing.")
        for label, files in dirty:
            print(f"  {label}:")
            for f in files[:10]:
                print(f"    {f}")
            if len(files) > 10:
                print(f"    ... and {len(files) - 10} more")
        sys.exit(1)

    # Rebase submodules first, then root
    failed = []
    succeeded = []

    print("Submodules:")
    for sub in submodules:
        sub_path = os.path.join(PROJECT_ROOT, sub)
        if not os.path.isdir(os.path.join(sub_path, ".git")) and not os.path.isfile(
            os.path.join(sub_path, ".git")
        ):
            print(f"  {sub}: skipped (not initialized)")
            continue
        if rebase_repo(sub_path, sub):
            succeeded.append(sub)
        else:
            failed.append(sub)

    print("Root:")
    if rebase_repo(PROJECT_ROOT, "root"):
        succeeded.append("root")
    else:
        failed.append("root")

    # Summary
    print(f"Succeeded: {len(succeeded)}, Failed: {len(failed)}")
    if failed:
        print("Failed repos:")
        for name in failed:
            print(f"  {name}")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
