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

from typing import Any
from typing import get_origin
from memoization import cached

_TYPE_NAME_RULES: tuple[tuple[str, str], ...] | None = None
"""Type name rules loaded from TypeSettings, None before first load attempt."""

_TYPE_NAME_RULES_LOADING: bool = False
"""Flag to prevent re-entrant loading during TypeSettings initialization."""

_TYPES_DURING_LOADING: list[type] = []
"""Types passed to typename during the loading phase, checked for conflicts after loading completes."""

_APPLY_RULES = None
"""Cached reference to TypeSettings.apply_type_name_rules static method."""


def _ensure_type_name_rules_loaded() -> None:
    """Load type name rules from TypeSettings on first call."""
    global _TYPE_NAME_RULES, _TYPE_NAME_RULES_LOADING, _APPLY_RULES
    if _TYPE_NAME_RULES is not None or _TYPE_NAME_RULES_LOADING:
        return
    _TYPE_NAME_RULES_LOADING = True
    try:
        from cl.runtime.settings.type_settings import TypeSettings  # noqa: inline import to avoid circular dependency

        _TYPE_NAME_RULES = TypeSettings.get_type_name_rules()
        _APPLY_RULES = TypeSettings.apply_type_name_rules
        # Clear cached typename results from during loading so they pick up rules
        typename.cache_clear()

        # Check that none of the types resolved during loading have custom names
        if _TYPE_NAME_RULES:
            conflicts = []
            for type_ in _TYPES_DURING_LOADING:
                qual = f"{type_.__module__}.{type_.__name__}"
                custom_name = _APPLY_RULES(_TYPE_NAME_RULES, qual)
                if custom_name != type_.__name__:
                    conflicts.append(f"  {qual} -> {custom_name}")
            if conflicts:
                conflicts_str = "\n".join(conflicts)
                raise RuntimeError(
                    f"Due to cyclic dependency, the following type names cannot be customized "
                    f"through TypeSettings.type_name_rules:\n{conflicts_str}"
                )
    except RuntimeError:
        raise
    except ImportError:
        # Circular import during module initialization, leave _TYPE_NAME_RULES as None to retry later
        _TYPE_NAME_RULES = None
    except Exception:
        # Fall back to no rules for other failures
        _TYPE_NAME_RULES = ()
    finally:
        _TYPE_NAME_RULES_LOADING = False
        _TYPES_DURING_LOADING.clear()


def typeof(value: Any) -> type:
    """Return type of the specified instance, converting ABCMeta and other metaclasses to type."""
    result = type(value)
    if issubclass(result, type):
        # If the result is a metaclass, convert to plain type
        result = type
    return result


@cached
def typename(type_: type) -> str:
    """
    Return type name without module in PascalCase, or a custom name from TypeSettings rules if provided.
    This method accepts type only, error if an instance is provided.
    """
    _ensure_type_name_rules_loaded()

    if isinstance(type_, type):
        # Collect types resolved during loading for conflict checking
        if _TYPE_NAME_RULES_LOADING:
            _TYPES_DURING_LOADING.append(type_)

        # Apply type name rules if loaded
        if _TYPE_NAME_RULES:
            qual = f"{type_.__module__}.{type_.__name__}"
            return _APPLY_RULES(_TYPE_NAME_RULES, qual)
        # Non-generic type, no rules
        return type_.__name__
    elif (type_origin := get_origin(type_)) is not None:
        # Parametrized generic including _GenericAlias
        return type_origin.__name__
    else:
        raise RuntimeError(
            f"Function typename accepts only type but an instance of {typename(type(type_))} was provided instead."
        )


def typenameof(value: Any) -> str:
    """Shortcut for typename(typeof(value))."""
    return typename(typeof(value))


def qualname(type_: type) -> str:
    """Return fully qualified type name with module in module.PascalCase format without applying any aliases."""
    # Accept type only, error if an instance is passed
    if isinstance(type_, type):
        return f"{type_.__module__}.{type_.__name__}"
    else:
        raise RuntimeError(
            f"Function qualname accepts only type but an instance of {qualname(type(type_))} was provided instead."
        )


def qualnameof(value: Any) -> str:
    """Shortcut for qualname(typeof(value))."""
    return typename(typeof(value))
