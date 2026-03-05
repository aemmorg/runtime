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
  1. uv     - fastest, modern resolver (uv pip compile)
  2. poetry - mature resolver (poetry lock, then lockfile graph walk)

Both tools support path dependencies to local packages, which is how
the project-level pyproject.toml references each sub-package.

The project-level pyproject.toml must already exist and contain path
dependencies referencing each package directory. Each package directory
must contain its own pyproject.toml with its own [project] dependencies.

Test dependencies from [dependency-groups] test are concatenated from all
packages without tree resolution and appended to the output.

Usage:
    python update_requirements.py
"""

# isort: off
# Ensure bootstrap module can be found and import to configure PYTHONPATH and other settings
# This code block must remain at the top before any other imports
import locate
locate.append_sys_path("../../..")
import cl.runtime.bootstrap  # noqa: F401
# isort: on

import platform
import subprocess
import sys
from pathlib import Path
from cl.runtime.project.project_util import ProjectUtil


# ---------------------------------------------------------------------------
# Tool discovery
# ---------------------------------------------------------------------------

def _venv_bin_dir() -> Path:
    """Return the venv's bin/Scripts directory for the running interpreter."""
    if platform.system() == "Windows":
        return Path(sys.prefix) / "Scripts"
    return Path(sys.prefix) / "bin"


def _which(name: str) -> str | None:
    """Return the absolute path of *name* if it is installed in the active venv, else None.

    Only the venv's own bin/Scripts directory is searched so that system-wide
    installations are never picked up by accident.
    """
    bin_dir = _venv_bin_dir()
    if platform.system() == "Windows":
        candidates = [bin_dir / f"{name}.exe", bin_dir / f"{name}.cmd", bin_dir / f"{name}.bat"]
    else:
        candidates = [bin_dir / name]
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None


def _find_resolver() -> tuple[str, str]:
    """Return (tool_name, executable_path) for the best available resolver.

    Raises RuntimeError when nothing is found.
    """
    for tool in ("uv", "poetry"):
        path = _which(tool)
        if path is not None:
            return tool, path

    raise RuntimeError(
        "No supported dependency resolver found in the active venv.\n"
        "Install one of the following:\n"
        "  pip install uv       (recommended, fastest)\n"
        "  pip install poetry   (alternative)\n"
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

import re

_NORMALISE_RE = re.compile(r"[-_.]+")


def _normalise_pkg_name(name: str) -> str:
    """PEP 503 normalisation: lowercase, collapse runs of [-_.] to single '-'."""
    return _NORMALISE_RE.sub("-", name).lower()


def _version_tuple(version: str) -> tuple[int, ...]:
    """Convert a version string like '3.6.1' into a comparable int tuple."""
    parts: list[int] = []
    for segment in version.split("."):
        try:
            parts.append(int(segment))
        except ValueError:
            break
    return tuple(parts)


def _collect_test_dep_names(project_root: str) -> set[str]:
    """Return normalised names of all test dependencies listed in pyproject.toml."""
    pyproject_path = Path(project_root) / "pyproject.toml"
    if not pyproject_path.exists():
        return set()

    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            return set()

    with open(pyproject_path, "rb") as fh:
        data = tomllib.load(fh)

    raw_deps = data.get("dependency-groups", {}).get("test", [])
    names: set[str] = set()
    for dep in raw_deps:
        # Strip version specifier: "pytest>=8.3.3" -> "pytest"
        match = re.split(r"[><=!~\[]", dep, maxsplit=1)
        if match:
            names.add(_normalise_pkg_name(match[0].strip()))
    return names


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
    """Resolve with ``poetry lock``, then walk the lockfile dependency graph.

    Poetry 2.x locks *all* groups (including ``[dependency-groups]``).
    There is no ``--only main`` flag for ``poetry lock``.  So after
    locking we parse the ``[[package]]`` array and walk the dependency
    graph starting from only the *main* ``[project] dependencies``,
    collecting reachable packages and ignoring anything that is only
    pulled in by a test dependency group.
    """
    print("Resolving dependency tree with Poetry...")

    # poetry lock (try --no-update first for speed)
    lock_result = None
    for extra_args in (["--no-update"], []):
        lock_result = subprocess.run(
            [poetry, "lock", *extra_args],
            cwd=project_root,
            capture_output=True,
            text=True,
        )
        if lock_result.returncode == 0:
            break

    if lock_result is None or lock_result.returncode != 0:
        raise RuntimeError(
            f"poetry lock failed (rc={lock_result.returncode if lock_result else 'N/A'}):\n"
            f"stdout: {lock_result.stdout if lock_result else ''}\n"
            f"stderr: {lock_result.stderr if lock_result else ''}"
        )

    # ---- parse lockfile & pyproject ----
    lockfile_path = Path(project_root) / "poetry.lock"
    if not lockfile_path.exists():
        raise RuntimeError(f"poetry.lock not found in {project_root} after running poetry lock.")

    try:
        import tomllib  # Python 3.11+
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    with open(lockfile_path, "rb") as fh:
        lock_data = tomllib.load(fh)

    pyproject_path = Path(project_root) / "pyproject.toml"
    with open(pyproject_path, "rb") as fh:
        pyproject_data = tomllib.load(fh)

    # Build lookup: normalised_name -> {version, deps[], is_path, markers}
    packages: dict[str, dict] = {}
    for pkg in lock_data.get("package", []):
        name = pkg.get("name", "")
        if not name:
            continue
        norm = _normalise_pkg_name(name)
        source = pkg.get("source", {})
        is_path = source.get("type") in ("directory", "file")
        markers = pkg.get("markers")

        # Collect this package's own dependencies (keys of the [dependencies] table)
        raw_deps = pkg.get("dependencies", {})
        dep_names = {_normalise_pkg_name(d) for d in raw_deps}

        entry = {
            "name": name,
            "version": pkg.get("version", ""),
            "deps": dep_names,
            "is_path": is_path,
            "markers": markers,
        }
        # Keep the highest version if duplicated
        if norm not in packages or _version_tuple(entry["version"]) > _version_tuple(packages[norm]["version"]):
            packages[norm] = entry

    # Determine main entry points from [project] dependencies
    main_deps_raw = pyproject_data.get("project", {}).get("dependencies", [])
    seeds: set[str] = set()
    for dep in main_deps_raw:
        name_part = re.split(r"[><=!~\[;]", dep, maxsplit=1)[0].strip()
        if name_part:
            seeds.add(_normalise_pkg_name(name_part))

    # BFS/DFS: walk from seeds, collecting all reachable packages
    visited: set[str] = set()
    queue = list(seeds)
    while queue:
        norm = queue.pop()
        if norm in visited:
            continue
        visited.add(norm)
        pkg_entry = packages.get(norm)
        if pkg_entry is None:
            continue
        for child in pkg_entry["deps"]:
            if child not in visited:
                queue.append(child)

    # Emit only visited packages, skip local path deps.
    # Preserve Python markers so pip/uv will skip inapplicable packages.
    lines: list[str] = []
    for norm in sorted(visited):
        pkg_entry = packages.get(norm)
        if pkg_entry is None:
            continue
        if pkg_entry["is_path"]:
            continue
        line = f"{pkg_entry['name']}=={pkg_entry['version']}"
        marker = pkg_entry["markers"]
        if marker:
            # Poetry 2.x: markers is a dict; use the "main" group marker
            if isinstance(marker, dict):
                marker = marker.get("main")
            if isinstance(marker, str) and marker.strip():
                line += f" ; {marker}"
        lines.append(line)

    return "\n".join(sorted(lines, key=lambda s: s.casefold()))


_RESOLVERS = {
    "uv": _resolve_with_uv,
    "poetry": _resolve_with_poetry,
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

    # Package dependencies (resolved) — skip editable installs and local path entries
    if package_deps.strip():
        lines.append("# Package dependencies (resolved)")
        for raw in package_deps.strip().splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            # Skip editable installs emitted for local path dependencies (e.g. "-e runtime")
            if line.startswith("-e "):
                continue
            # Skip bare local path entries (e.g. "file:///..." or relative paths without version spec)
            if line.startswith("file:"):
                continue
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

def update_requirements() -> None:
    """Resolve full dependency tree and write unified requirements.txt."""
    project_root = ProjectUtil.get_project_root()
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
    update_requirements()

