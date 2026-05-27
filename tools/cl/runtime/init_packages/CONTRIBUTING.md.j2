# Contributing

This guide covers development setup, workflow, and coding standards.

## Getting Started

### Prerequisites

- Python 3.11 or later
- Git

### Setup

Create and activate the virtual environment, then install dependencies:

```bash
# Windows
init_venv.cmd
call activate.cmd

# Linux/macOS
./init_venv.sh
source activate.sh

# Install dependencies (including test/dev tools)
pip install --group test .
```

### Regenerate Type Info

When adding or changing fields or inheritance in a class that inherits from a framework
base (e.g., `DataMixin`, `RecordMixin`, `KeyMixin`), regenerate the type cache:

```bash
# Windows
init_type_info.cmd

# Linux/macOS (from project root)
PYTHONPATH="submodule1;submodule2" .venv/bin/python -m tools.cl.runtime.init_type_info
```

This updates `resources/bootstrap/TypeInfo.csv` which maps type names to their fully
qualified module paths.

### Initialize Database

```bash
# Windows
init_db.cmd

# Linux/macOS (from project root)
PYTHONPATH="submodule1;submodule2" .venv/bin/python -m tools.cl.runtime.init_db
```

## Development Workflow

### Running Formatters

```bash
run_formatters.cmd   # Windows
./run_formatters.sh  # Linux/macOS
```

### Running Linters

```bash
run_linters.cmd   # Windows
./run_linters.sh  # Linux/macOS
```

### Running Tests

```bash
# From project root (runs tests for all packages)
run_tests.cmd

# Or run pytest directly
pytest tests
```

### Pull Request Process

1. Create a feature branch from `develop`
2. Make changes following the coding standards below
3. Run formatters, linters, and tests
4. Regenerate `TypeInfo.csv` if class hierarchy changed
5. Commit with proper message format (see Git Commit Messages)
6. Submit PR against `develop`

## Coding Standards

### Line Length

120 characters, enforced by black.

### Required Header

All files must begin with the contents of the COPYRIGHT file at package root,
prefixed by comment symbol, `#` in case of Python, followed by a space.

### Module Structure

1. **License header**
2. **Imports** (sorting enforced by isort via `run_formatters`)
3. **Module-level constants and variables**
4. **Classes and functions**
5. **Module-level execution code** (if any)

### Class Member Organization

1. **Class docstring**
2. **Class-level constants / ClassVar / `__slots__`**
3. **Fields** (for `@dataclass`/`attrs`)
4. **Constructors** (`__new__`, `__init__`, `__post_init__`)
5. **Protocol/dunder behavior** (`__repr__`, `__str__`, comparisons, context manager)
6. **Alternative constructors** (`@classmethod` like `from_*`)
7. **Properties** (`@property` + setter/deleter kept together)
8. **Public instance methods**
9. **Public `@classmethod` / `@staticmethod`**
10. **Protected methods** (`_*`)
11. **Private/mangled methods** (`__*`) if necessary

### Dataclasses

Use `@dataclass(slots=True, kw_only=True)` and `required()` for mandatory fields:

```python
@dataclass(slots=True, kw_only=True)
class DataSerializer(Serializer):
    """Roundtrip serialization of object to dictionary with optional type information."""

    primitive_serializer: Serializer = required()
    """Use to serialize primitive types."""

    enum_serializer: Serializer = required()
    """Use to serialize enum types."""

    key_serializer: Serializer | None = None
    """Use to serialize key fields if specified, otherwise serialize the same way as data fields."""
```

### Abstract Base Classes

```python
@dataclass(slots=True, kw_only=True)
class Serializer(BootstrapMixin, ABC):
    """Abstract base class of serializers that convert from one data representation to another."""

    @abstractmethod
    def serialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Serialize data to a dictionary."""

    @abstractmethod
    def deserialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
        """Deserialize a dictionary into object using type information extracted from the _type field."""
```

### Type Hints

- Use `|` for union types (not `Optional` or `Union`)
- Use `dict`, `list`, `tuple` builtins (not `Dict`, `List`, `Tuple` from typing)
- Use `type[T]` for class types

```python
def load_many(
    self,
    records_or_keys: Sequence[TRecord | TKey | None] | None,
    *,
    dataset: str | None = None,
    cast_to: type[TRecord] | None = None,
) -> Sequence[TRecord | None] | None:
```

### Type Variables

```python
from typing import TypeVar

TRecord = TypeVar("TRecord", bound=RecordProtocol)
TKey = TypeVar("TKey", bound=KeyProtocol)
```

### Keyword-Only Arguments

Use `*` to separate required positional parameters from optional keyword-only parameters:

```python
def load_table(
    self,
    table: str,
    *,
    dataset: str | None = None,
    cast_to: type[TRecord] | None = None,
    filter_to: type[TRecord] | None = None,
    project_to: type[TRecord] | None = None,
    limit: int | None = None,
    skip: int | None = None,
) -> tuple[TRecord]:
```

### Error Handling

Use `ErrorUtil` for consistent error messages and guard clauses for preconditions:

```python
if self.type_inclusion not in [TypeInclusion.AS_NEEDED, TypeInclusion.ALWAYS, TypeInclusion.OMIT]:
    raise ErrorUtil.enum_value_error(self.type_inclusion, TypeInclusion)

data_class_name = TypeUtil.name(data)
if data_class_name == "NoneType":
    if type_hint is None or is_optional:
        return None
    else:
        raise ErrorUtil.null_value_error("data")
```

```python
def _not_primitive_field_error(cls, data: RecordProtocol, k: str, v: Any) -> None:
    """Error indicating only primitive field names are supported."""
    supported_types = ", ".join(PRIMITIVE_CLASS_NAMES)
    raise RuntimeError(
        f"Field '{k}' in '{data.__class__.__name__}' has type '{type(v)}'.\n"
        f"This field cannot be used in a database filter because it is not one of the\n"
        f"supported primitive class names: {supported_types}."
    )
```

### Class Methods and `Self`

Use `Self` return type for class methods that return the class instance:

```python
@classmethod
def current(cls) -> Self:
    """Return the context from the innermost 'with' for cls.key_type(), error outside the outermost 'with'."""

    result = cls.current_or_none()
    if result:
        return result
    else:
        raise RuntimeError(
            f"{TypeUtil.name(cls)}.current() is undefined outside the outermost 'with {TypeUtil.name(cls)}(...)' clause.\n"
            f"To receive None instead of an exception, use {TypeUtil.name(cls)}.current_or_none()\n"
        )
```

### Docstrings

Follow Google-style format with `Args` and `Returns` sections:

```python
def serialize(self, data: Any, type_hint: TypeHint | None = None) -> Any:
    """
    Serialize a primitive type to a string or another primitive type.

    Args:
        data: The data to serialize
        type_hint: Optional type hint for serialization

    Returns:
        A string or another serialization output such as int or None
    """
```

## Import Guidelines

**Never use inline imports to resolve circular import issues.** All imports must be at the top of the file following standard Python conventions.

If you encounter circular import problems:
1. First, try to find a proper architectural solution (e.g., dependency injection, restructuring modules, using protocols/abstract base classes)
2. If the circular dependency seems unavoidable, pause and request instructions from the user rather than using inline imports as a workaround

Inline imports make code harder to understand, violate PEP 8 style guidelines, and hide architectural problems that should be resolved properly.


### Naming Conventions

- Boolean variables use auxiliary verbs: `is_active`, `has_permission`
- Class names use descriptive suffixes: `Serializer`, `Context`, `Manager`
- Module-level constants use inline docstrings:

```python
invalid_db_name_symbols = r'/\\. "$*<>:|?'
"""Invalid MongoDB database name symbols."""
```

### Settings

Settings classes use Dynaconf to load configuration from YAML files and environment variables.
Each subclass of `Settings` has a prefix derived from the class name by converting to snake_case
and removing the `Settings` suffix (e.g., `ApiSettings` → `api_`, `DbSettings` → `db_`).
All fields in the class must start with this prefix, and only Dynaconf fields matching
the prefix are passed to the constructor.

```python
@dataclass(slots=True, kw_only=True)
class ApiSettings(Settings):
    """Configuration for the API server."""

    api_host: str = "localhost"
    """API server hostname."""

    api_port: int = 7008
    """API server port."""
```

The `instance()` method returns a cached singleton. Without `package`, it loads from
the project root directory. With `package`, it loads from the package directory instead
(e.g., `runtime/` for `cl.runtime`). These are independent — package settings are not
merged with root settings.

```python
# Load from project root (settings.yaml, envvar prefix CL_)
api_settings = ApiSettings.instance()

# Load from package directory runtime/ (cl.runtime.settings.yaml, envvar prefix CL_RUNTIME_)
package_settings = PackageSettings.instance(package="cl.runtime")
```

Within each context, sources are merged in this priority order (highest first):

1. OS environment variables (prefix `CL_` for root, `CL_RUNTIME_` for `cl.runtime`)
2. `.env` file
3. `{filename}.local.yaml` (local overrides, not committed)
4. `.secrets.yaml`
5. `{filename}.yaml` (baseline defaults)

Where `{filename}` is `settings` for root or `{namespace}.settings` for packages
(e.g., `cl.runtime.settings`).

## Testing Standards

### Test Organization

- Test directory structure mirrors source: `tests/cl/runtime/...` mirrors `cl/runtime/...`
- Test files are named `test_*.py`
- Group related tests in classes with `Test` prefix

```python
class TestApplyEnvConfig:
    """Tests for apply_env_config."""

    def test_sets_env_var(self):
        ...

class TestActivateDataSource:
    """Tests for activate_data_source context manager."""

    def test_creates_contexts_and_yields(self):
        ...
```

### Fixtures

Define shared fixtures in `conftest.py` at the package test root. Key fixtures are
provided by `cl.runtime.qa.pytest.pytest_fixtures`:

- `basic_mongo_db_fixture` - MongoDB database
- `basic_mongo_mock_db_fixture` - Mocked MongoDB (no server required)
- `sqlite_db_fixture` - SQLite database
- `default_db_fixture` - Default configured database
- `work_dir_fixture` - Temporary working directory
- `configure_logging_fixture` - Logging configuration
- `tenant_fixture` - Parameterized tenant fixture

### Mock Classes

```python
@dataclass(slots=True, kw_only=True)
class BasicMongoMockDb(BasicMongoDb):
    """Mock MongoDB database for testing without datasets."""

    def _get_mongo_client(self) -> MongoClientMock:
        """Get mock MongoDB client for testing."""
        return MongoClientMock()
```

## Git Commit Messages

### Subject Line

- Start with a capital letter
- Use imperative mood ("Fix bug" not "Fixed bug")
- Do **not** end with a period
- Keep under 72 characters

### Body (Optional)

- Separate from the subject with a blank line
- Write in normal prose with full sentences, capitalization, and periods
- Wrap at 72 characters

### Examples

**Subject only:**
```
Fix null pointer exception in user login
```

**Subject with body:**
```
Fix null pointer exception in user login

The login handler was not checking for null when the session
token expired during validation. This caused a crash for users
with stale cookies. Added a null check and redirect to the
login page when the token is missing.
```
