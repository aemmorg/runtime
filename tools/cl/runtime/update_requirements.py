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

"""
Standalone tool to resolve the full dependency tree for the project and
generate a unified requirements.txt at the project root.

Resolution strategy (first available tool wins):
  1. uv   - fastest, modern resolver (uv pip compile)
  2. poetry - mature resolver (poetry lock && poetry export)
  3. pip-compile - pip-tools resolver

The project-level pyproject.toml must already exist and contain path
dependencies referencing each package directory. Each package directory
must contain its own pyproject.toml with its own [project] dependencies.

Test dependencies from [dependency-groups] test are concatenated from all
packages without tree resolution and appended to the output.

Usage:
    python update_requirements.py --project-root <path>
"""

import argparse
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Tool discovery
# ---------------------------------------------------------------------------

def _which(name: str) -> str | None:
    """Return the absolute path of *name* if found on PATH, else None."""
    return shutil.which(name)


def _find_resolver() -> tuple[str, str]:
    """Return (tool_name, executable_path) for the best available resolver.

    Raises RuntimeError when nothing is found.
    """
    for tool in ("uv", "poetry", "pip-compile"):
        path = _which(tool)
        if path is not None:
            return tool, path

    raise RuntimeError(
        "No supported dependency resolver found on PATH.\n"
        "Install one of the following:\n"
        "  pip install uv          (recommended, fastest)\n"
        "  pip install poetry       (alternative)\n"
        "  pip install pip-tools    (provides pip-compile)\n"
    )


# ---------------------------------------------------------------------------
# Resolvers
# ---------------------------------------------------------------------------

def _resolve_with_uv(uv: str, project_root: str) -> str:
    """Resolve with ``uv pip compile pyproject.toml``."""
    print("Resolving dependency tree with uv...")
    result = subprocess.run(
        [uv, "pip", "compile", "pyproject.toml", "--no-header", "--quiet"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"uv pip compile failed (rc={result.returncode}):\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.stdout


def _resolve_with_poetry(poetry: str, project_root: str) -> str:
    """Resolve with ``poetry lock`` + ``poetry export``."""
    print("Resolving dependency tree with Poetry...")

    # poetry lock (try --no-update first for speed, fall back to full lock)
    lock = None
    for extra_args in (["--no-update"], []):
        lock = subprocess.run(
            [poetry, "lock", *extra_args],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if lock.returncode == 0:
            break

    if lock is None or lock.returncode != 0:
        raise RuntimeError(
            f"poetry lock failed (rc={lock.returncode if lock else 'N/A'}):\n"
            f"stdout: {lock.stdout if lock else ''}\nstderr: {lock.stderr if lock else ''}"
        )

    # poetry export
    export = subprocess.run(
        [poetry, "export", "-f", "requirements.txt", "--without-hashes"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    if export.returncode != 0:
        raise RuntimeError(
            f"poetry export failed (rc={export.returncode}):\n"
            f"stdout: {export.stdout}\nstderr: {export.stderr}"
        )
    return export.stdout


def _resolve_with_pip_compile(pip_compile: str, project_root: str) -> str:
    """Resolve with ``pip-compile pyproject.toml``."""
    print("Resolving dependency tree with pip-compile...")
    # Write to a temp file, then read back
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", dir=project_root, delete=False
    ) as tmp:
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            [
                pip_compile,
                "pyproject.toml",
                "--output-file", tmp_path,
                "--no-header",
                "--no-annotate",
                "--quiet",
            ],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"pip-compile failed (rc={result.returncode}):\n"
                f"stdout: {result.stdout}\nstderr: {result.stderr}"
            )
        return Path(tmp_path).read_text(encoding="utf-8")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


_RESOLVERS = {
    "uv": _resolve_with_uv,
    "poetry": _resolve_with_poetry,
    "pip-compile": _resolve_with_pip_compile,
}


# ---------------------------------------------------------------------------
# Test-dependency collection
# ---------------------------------------------------------------------------

def _collect_test_dependencies(project_root: str) -> list[str]:
    """Read [dependency-groups] test from pyproject.toml (plain concatenation)."""
    pyproject_path = Path(project_root) / "pyproject.toml"
    if not pyproject_path.exists():
        return []

    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            print("Warning: tomllib/tomli unavailable — skipping test deps")
            return []

    with open(pyproject_path, "rb") as fh:
        data = tomllib.load(fh)

    return list(data.get("dependency-groups", {}).get("test", []))


# ---------------------------------------------------------------------------
# Writer
# ---------------------------------------------------------------------------

def _write_requirements(
    project_root: str,
    package_deps: str,
    test_deps: list[str],
    tool_name: str,
) -> None:
    """Write the unified requirements.txt at *project_root*."""
    requirements_path = Path(project_root) / "requirements.txt"
    nl = "\r\n" if platform.system() == "Windows" else "\n"

    lines: list[str] = [
        f"# Auto-generated by update_requirements.py ({tool_name})",
        "# Do not edit manually — run init_project or update_requirements to regenerate",
        "",
    ]

    # Package dependencies (resolved)
    if package_deps.strip():
        lines.append("# Package dependencies (resolved)")
        for raw in package_deps.strip().splitlines():
            line = raw.strip()
            if line and not line.startswith("#"):
                lines.append(line)
        lines.append("")

    # Test dependencies (concatenated, not resolved)
    if test_deps:
        lines.append("# Test dependencies")
        lines.extend(test_deps)
        lines.append("")

    content = nl.join(lines)
    with open(requirements_path, "w", encoding="utf-8", newline="") as fh:
        fh.write(content)

    print(f"Written {requirements_path}")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def update_requirements(project_root: str) -> None:
    """Resolve full dependency tree and write unified requirements.txt."""
    pyproject_path = Path(project_root) / "pyproject.toml"
    if not pyproject_path.exists():
        raise RuntimeError(
            f"pyproject.toml not found in {project_root}. Run init_project first."
        )

    tool_name, tool_path = _find_resolver()
    print(f"Using {tool_name} ({tool_path})")

    package_deps = _RESOLVERS[tool_name](tool_path, project_root)
    test_deps = _collect_test_dependencies(project_root)
    _write_requirements(project_root, package_deps, test_deps, tool_name)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Resolve dependency tree and generate unified requirements.txt",
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Absolute path to the project root containing pyproject.toml",
    )
    args = parser.parse_args()
    update_requirements(os.path.abspath(args.project_root))

