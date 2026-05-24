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

import ast
import subprocess
import sys
from typing import Sequence
from cl.runtime.prebuild.source_util import SourceUtil

_MAX_CMD_BATCH = 200
"""Maximum number of file paths per isort invocation to stay within command-line length limits."""


class InlineImportsUtil:
    """Helper class for detecting and fixing inline imports (import statements inside function or method bodies)."""

    @classmethod
    def guard_no_inline_imports(
        cls,
        *,
        raise_on_fail: bool = True,
        verbose: bool = True,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> bool:
        """Test that no import statements exist inside function or method bodies.

        Raises RuntimeError with a detailed list of files and lines with inline imports.

        Args:
            raise_on_fail: If True, raise RuntimeError on invalid type, otherwise return None
            verbose: Print messages about errors or fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """
        if file_exclude_patterns is None:
            file_exclude_patterns = ["stub_inline_imports*"]

        source_files = SourceUtil.get_abs_source_files(
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        error_files: dict[str, list[tuple[int, str]]] = {}
        for file_path in source_files:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            inline_imports = cls._find_inline_imports(source, file_path)
            if inline_imports:
                file_errors: list[tuple[int, str]] = []
                for node, start_line, _ in inline_imports:
                    for text in cls._import_node_to_lines(node):
                        file_errors.append((start_line, text))
                error_files[file_path] = file_errors

        if error_files:
            if raise_on_fail or verbose:
                # Create file list
                total = sum(len(v) for v in error_files.values())
                parts = [f"Found {total} inline import(s) in {len(error_files)} file(s):\n"]
                for file_path, imports in error_files.items():
                    parts.append(f"  {file_path}")
                    for line_no, text in imports:
                        parts.append(f"    line {line_no}: {text}")
                error_msg = "\n".join(parts)

                # Raise an error or print
                if raise_on_fail:
                    raise RuntimeError(error_msg)
                elif verbose:
                    print(error_msg)

            # Errors found
            return False
        else:
            # No errors found
            return True

    @classmethod
    def fix_inline_imports(
        cls,
        *,
        verbose: bool = False,
        file_include_patterns: Sequence[str] | None = None,
        file_exclude_patterns: Sequence[str] | None = None,
    ) -> None:
        """Move inline imports to the top of each file and run isort to sort them.

        Skips files where removal of inline imports would cause syntax errors.

        Args:
            verbose: Print messages about fixes to stdout if specified
            file_include_patterns: Optional list of filename glob patterns to include
            file_exclude_patterns: Optional list of filename glob patterns to exclude
        """
        if file_exclude_patterns is None:
            file_exclude_patterns = ["stub_inline_imports*"]

        source_files = SourceUtil.get_source_files(
            file_include_patterns=file_include_patterns,
            file_exclude_patterns=file_exclude_patterns,
        )

        if not source_files:
            if verbose:
                print("No source files found.")
            return

        fixed_files: list[str] = []
        skipped_files: list[str] = []

        for file_path in source_files:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            inline_imports = cls._find_inline_imports(source, file_path)
            if not inline_imports:
                continue

            lines = source.split("\n")

            # Collect line indices to remove (0-based) and import texts to add
            remove_indices: set[int] = set()
            import_texts: list[str] = []
            for node, start_line, end_line in inline_imports:
                for line_idx in range(start_line - 1, end_line):
                    remove_indices.add(line_idx)
                import_texts.extend(cls._import_node_to_lines(node))

            # Remove inline import lines
            new_lines = [line for i, line in enumerate(lines) if i not in remove_indices]

            # Verify the modified source still parses
            try:
                ast.parse("\n".join(new_lines), filename=file_path)
            except SyntaxError:
                skipped_files.append(file_path)
                continue

            # Find insertion point and add imports
            insert_pos = cls._find_import_insert_position(new_lines)
            for j, text in enumerate(import_texts):
                new_lines.insert(insert_pos + j, text)

            # Write back
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(new_lines))

            fixed_files.append(file_path)

        # Run isort on all modified files to sort imports properly
        if fixed_files:
            cls._run_isort(fixed_files)

        if verbose:
            if fixed_files:
                print(
                    f"Fixed inline imports in {len(fixed_files)} file(s):\n"
                    + "".join(f"    {f}\n" for f in fixed_files)
                )
            if skipped_files:
                print(
                    f"Skipped {len(skipped_files)} file(s) (removal would cause syntax errors):\n"
                    + "".join(f"    {f}\n" for f in skipped_files)
                )
            if not fixed_files and not skipped_files:
                print("No inline imports found.")

    @classmethod
    def _import_node_to_lines(cls, node: ast.Import | ast.ImportFrom) -> list[str]:
        """Convert an AST import node to top-level import statement strings.

        Args:
            node: An ast.Import or ast.ImportFrom node

        Returns:
            List of import statement strings (one per imported name for force_single_line compatibility).
        """
        results = []
        if isinstance(node, ast.Import):
            for alias in node.names:
                text = f"import {alias.name}"
                if alias.asname:
                    text += f" as {alias.asname}"
                results.append(text)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            prefix = "." * (node.level or 0)
            full_module = prefix + module
            for alias in node.names:
                text = f"from {full_module} import {alias.name}"
                if alias.asname:
                    text += f" as {alias.asname}"
                results.append(text)
        return results

    @classmethod
    def _find_inline_imports_after_code_begins(
        cls,
        source: str,
        file_path: str,
    ) -> list[ast.Import | ast.ImportFrom]:
        """Find import statements that appear after the first non-import code in the file.

        Heuristic: scans top-level statements to find the first one that is not an import
        or a module docstring, then flags any import at any nesting level whose line number
        is at or after that point.

        Args:
            source: File source code
            file_path: Path for error reporting

        Returns:
            List of ast.Import / ast.ImportFrom nodes ordered by line number.
        """
        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError:
            return []

        code_start_line: int | None = None
        for stmt in tree.body:
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                continue
            # Skip bare expression statements (module docstrings, setup calls like locate.append_sys_path)
            if isinstance(stmt, ast.Expr):
                continue
            code_start_line = stmt.lineno
            break

        if code_start_line is None:
            return []

        inline_imports: list[ast.Import | ast.ImportFrom] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            if node.lineno < code_start_line:
                continue
            inline_imports.append(node)

        inline_imports.sort(key=lambda n: n.lineno)
        return inline_imports

    @classmethod
    def _find_inline_imports(
        cls,
        source: str,
        file_path: str,
    ) -> list[tuple[ast.Import | ast.ImportFrom, int, int]]:
        """Find import statements inside function or method bodies.

        Args:
            source: File source code
            file_path: Path for error reporting

        Returns:
            List of (node, start_line, end_line) tuples with 1-based line numbers.
        """
        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError:
            return []

        # Collect line ranges of all function and async function definitions
        func_ranges: list[tuple[int, int]] = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_ranges.append((node.lineno, node.end_lineno or node.lineno))

        if not func_ranges:
            return []

        # Find import nodes whose line numbers fall within a function range
        inline_imports: list[tuple[ast.Import | ast.ImportFrom, int, int]] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            for func_start, func_end in func_ranges:
                if func_start <= node.lineno <= func_end:
                    end_line = node.end_lineno or node.lineno
                    inline_imports.append((node, node.lineno, end_line))
                    break

        inline_imports.sort(key=lambda x: x[1])
        return inline_imports

    @classmethod
    def _find_import_insert_position(cls, lines: list[str]) -> int:
        """Find the 0-based line index where new top-level imports should be inserted.

        Finds the position after the last top-level (non-indented) import statement.
        If no imports exist, returns the position after the copyright header.

        Args:
            lines: Source file lines (without line endings)

        Returns:
            0-based line index for insertion.
        """
        last_import = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if line and not line[0].isspace() and (stripped.startswith("import ") or stripped.startswith("from ")):
                if "(" in stripped and ")" not in stripped:
                    # Multi-line import, find closing parenthesis
                    j = i
                    while j < len(lines) and ")" not in lines[j]:
                        j += 1
                    last_import = j
                else:
                    last_import = i

        if last_import >= 0:
            return last_import + 1

        # No imports found, insert after copyright header and blank line
        header_end = 0
        for i, line in enumerate(lines):
            if line.startswith("#"):
                header_end = i + 1
            else:
                break
        while header_end < len(lines) and lines[header_end].strip() == "":
            header_end += 1
        return header_end

    @classmethod
    def _run_isort(cls, file_paths: list[str]) -> None:
        """Run isort on the given files to sort top-level imports.

        Args:
            file_paths: List of absolute file paths to process
        """
        for i in range(0, len(file_paths), _MAX_CMD_BATCH):
            batch = file_paths[i : i + _MAX_CMD_BATCH]
            subprocess.run([sys.executable, "-m", "isort"] + batch, capture_output=True, text=True)
