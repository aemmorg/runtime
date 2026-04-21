# Feature: Variants and DataContainers

## Overview

Unified type-wrapper package for polymorphic UI values. Two independent hierarchies live in `cl.runtime.records.variant`:

- **Variant** -- single-cell value wrappers for polymorphic data in table cells, key-value pairs, and handler arguments
- **DataContainer** -- column-vector wrappers for `TreeTableControl` columns

Both extend `DataclassMixin` independently and follow the standard builder pattern (`@dataclass(slots=True, kw_only=True)`, `.build()` to freeze).

**Design rationale:** Tables and controls need to store values whose concrete type varies per cell or column. Rather than using `Any` or unions in schemas, each value is wrapped in a typed Variant subclass. The schema system introspects these types via `TypeInfo.csv`, enabling the UI to deserialize them polymorphically.

---

## Class Hierarchy

```
records/variant/

Variant (DataclassMixin, ABC)                     [single values]
|   metadata: DataclassMixin | None
|
+-- PrimitiveVariant (ABC)                        [scalar primitives]
|   +-- StrVariant          value: str
|   +-- IntVariant          value: int
|   +-- BoolVariant         value: bool
|   +-- FloatVariant        value: float
|   +-- DateTimeVariant     value: datetime.datetime
|   +-- DateVariant         value: datetime.date
|   +-- TimeVariant         value: datetime.time
|
+-- ListVariant             value: list[Variant]  [recursive collection]
|
+-- DataMixinVariant (ABC)                        [record/key wrappers]
    +-- KeyVariant          value: KeyMixin
    +-- DataVariant         value: DataclassMixin

DataContainer (DataclassMixin, ABC)               [column vectors]
+-- TextContainer           data: list[str | None]
|   +-- TreeContainer       data: list[str | None], node_separator: str
+-- NumericContainer        data: list[float | None]
+-- KeyContainer            data: list[KeyMixin | None]
+-- DateContainer           data: list[datetime.date | None]
```

`Variant` and `DataContainer` are **separate bases** -- both extend `DataclassMixin` independently but are co-located in the same package because they serve the same purpose of typed data wrapping for UI controls.

---

## Files

All paths relative to `runtime/cl/runtime/records/variant/`.

### Variant Hierarchy

| File | Class | Inherits | Fields |
|------|-------|----------|--------|
| `variant.py` | `Variant` | `DataclassMixin, ABC` | `metadata: DataclassMixin \| None` |
| `primitive_variant.py` | `PrimitiveVariant` | `Variant, ABC` | (none -- intermediate) |
| `str_variant.py` | `StrVariant` | `PrimitiveVariant` | `value: str` |
| `int_variant.py` | `IntVariant` | `PrimitiveVariant` | `value: int` |
| `bool_variant.py` | `BoolVariant` | `PrimitiveVariant` | `value: bool` |
| `float_variant.py` | `FloatVariant` | `PrimitiveVariant` | `value: float` |
| `date_time_variant.py` | `DateTimeVariant` | `PrimitiveVariant` | `value: datetime.datetime` |
| `date_variant.py` | `DateVariant` | `PrimitiveVariant` | `value: datetime.date` |
| `time_variant.py` | `TimeVariant` | `PrimitiveVariant` | `value: datetime.time` |
| `list_variant.py` | `ListVariant` | `Variant` | `value: list[Variant]` |
| `data_mixin_variant.py` | `DataMixinVariant` | `Variant, ABC` | (none -- intermediate) |
| `key_variant.py` | `KeyVariant` | `DataMixinVariant` | `value: KeyMixin` |
| `data_variant.py` | `DataVariant` | `DataMixinVariant` | `value: DataclassMixin` |

### Factory

| File | Class | Description |
|------|-------|-------------|
| `variant_util.py` | `VariantUtil` | Static `create()` factory dispatching raw values to the correct Variant subclass |

### DataContainer Hierarchy

| File | Class | Inherits | Fields |
|------|-------|----------|--------|
| `data_container.py` | `DataContainer` | `DataclassMixin, ABC` | (none -- abstract base) |
| `text_container.py` | `TextContainer` | `DataContainer` | `data: list[str \| None]` |
| `numeric_container.py` | `NumericContainer` | `DataContainer` | `data: list[float \| None]` |
| `key_container.py` | `KeyContainer` | `DataContainer` | `data: list[KeyMixin \| None]` |
| `date_container.py` | `DateContainer` | `DataContainer` | `data: list[datetime.date \| None]` |
| `tree_container.py` | `TreeContainer` | `TextContainer` | `node_separator: str` (inherits `data` from TextContainer) |

---

## VariantUtil.create() Factory

`VariantUtil.create(value, metadata=None)` wraps a raw Python value into the appropriate Variant subclass based on its runtime type.

### Dispatch Order

The ordering is significant because of Python's type hierarchy (bool subclasses int, datetime subclasses date):

| Priority | Condition | Result |
|----------|-----------|--------|
| 1 | `isinstance(value, Variant)` | Passthrough (return same object) |
| 2 | `isinstance(value, bool)` | `BoolVariant` (must precede int) |
| 3 | `isinstance(value, int)` | `IntVariant` |
| 4 | `isinstance(value, float)` | `FloatVariant` |
| 5 | `isinstance(value, datetime.datetime)` | `DateTimeVariant` (must precede date) |
| 6 | `isinstance(value, datetime.date)` | `DateVariant` |
| 7 | `isinstance(value, datetime.time)` | `TimeVariant` |
| 8 | `isinstance(value, (list, tuple))` | `ListVariant` (recursive) |
| 9 | `isinstance(value, KeyMixin)` | `KeyVariant` (must precede DataclassMixin) |
| 10 | `isinstance(value, DataclassMixin)` | `DataVariant` |
| 11 | Fallback | `StrVariant(value=str(value))` |

### Metadata

The optional `metadata` parameter attaches arbitrary `DataclassMixin` data (e.g., tooltip configuration, button containers) to any Variant. When a Variant is passed through (priority 1), the original metadata is preserved and the new metadata parameter is ignored.

---

## Variant Base Class

```python
from abc import ABC
from dataclasses import dataclass
from cl.runtime.records.for_dataclasses.dataclass_mixin import DataclassMixin

@dataclass(slots=True, kw_only=True)
class Variant(DataclassMixin, ABC):
    """Wrapper for values used in UI layers when a schema cannot
    express a single concrete type."""

    metadata: DataclassMixin | None = None
    """Metadata for additional value characteristics."""
```

All Variant subclasses follow the same pattern -- a single `value` field with the appropriate type annotation. They use the standard `@dataclass(slots=True, kw_only=True)` decorator and support the builder pattern (`.build()` to freeze).

---

## DataContainer Classes

DataContainers hold column-oriented data for `TreeTableControl`. Each container represents one column; the `columns` and `data` lists in `TreeTableControl` are parallel arrays.

### TextContainer

Holds one string per row. Used for plain text columns.

```python
from cl.runtime.records.variant.text_container import TextContainer

col = TextContainer(data=["Alice", "Bob", None]).build()
```

### NumericContainer

Holds one float per row. Used for numeric columns.

```python
from cl.runtime.records.variant.numeric_container import NumericContainer

col = NumericContainer(data=[100.0, 200.5, None]).build()
```

### KeyContainer

Holds one `KeyMixin` per row. Used for columns that reference record keys.

```python
from cl.runtime.records.variant.key_container import KeyContainer

col = KeyContainer(data=[FooKey(id="a"), FooKey(id="b"), None]).build()
```

### DateContainer

Holds one `datetime.date` per row. Used for date columns.

```python
from cl.runtime.records.variant.date_container import DateContainer

col = DateContainer(data=[date(2025, 1, 1), date(2025, 6, 30), None]).build()
```

### TreeContainer

Extends `TextContainer` with a separator for hierarchical row labels. The first column of a `TreeTableControl` is typically a `TreeContainer`.

```python
from cl.runtime.records.variant.tree_container import TreeContainer

col = TreeContainer(
    data=["Revenue", "Revenue.Product", "Revenue.Services", "Expenses"],
    node_separator=".",
).build()
```

---

## Usage Examples

### Wrapping values for a TableControl

```python
from cl.runtime.records.variant.variant_util import VariantUtil
from cl.runtime.ui.control.table_control import TableControl

table = TableControl(
    control_path="Table",
    col_names=["Name", "Value", "Active"],
    data=[
        VariantUtil.create("Widget"),
        VariantUtil.create(42),
        VariantUtil.create(True),
    ],
)
table.init()
```

### Wrapping values with metadata

```python
from cl.runtime.records.variant.variant_util import VariantUtil

tooltip = SomeTooltipData(text="Click for details")
cell = VariantUtil.create("$680.00", metadata=tooltip)
# cell is StrVariant(value="$680.00", metadata=SomeTooltipData(...))
```

### Wrapping keys and records

```python
from cl.runtime.records.variant.variant_util import VariantUtil

key = StubDataclassKey(id="abc")
variant = VariantUtil.create(key)
# variant is KeyVariant(value=StubDataclassKey(id="abc"))

data = StubDataclassData(str_field="test")
variant = VariantUtil.create(data)
# variant is DataVariant(value=StubDataclassData(str_field="test"))
```

### Building a TreeTableControl

```python
from cl.runtime.records.variant.text_container import TextContainer
from cl.runtime.records.variant.tree_container import TreeContainer
from cl.runtime.records.variant.numeric_container import NumericContainer
from cl.runtime.ui.control.tree_table_control import TreeTableControl
from cl.runtime.ui.control.configs.column_config import ColumnConfig

tree_table = TreeTableControl(
    control_path="TreeTable",
    columns=[
        ColumnConfig(name="Category"),
        ColumnConfig(name="Q1"),
        ColumnConfig(name="Q2"),
    ],
    data=[
        TreeContainer(
            data=["Revenue", "Revenue.Product", "Revenue.Services"],
            node_separator=".",
        ),
        NumericContainer(data=[1000.0, 600.0, 400.0]),
        NumericContainer(data=[1200.0, 700.0, 500.0]),
    ],
)
```

---

## Consumer Files

### Variant consumers (import `Variant` or `VariantUtil`)

| File | Usage |
|------|-------|
| `ui/control/table_control.py` | `data: list[Variant]` field type |
| `ui/control/key_value_control.py` | `VariantUtil.create()` in `set_data()` |
| `ui/control/key_value_cell_control.py` | `value: Variant` field type |
| `ui/control/core/handler_parameters.py` | `arguments: dict[str, Variant]` field type |
| `tests/cl/runtime/ui/test_control_events.py` | `VariantUtil.create()` and `StrVariant` assertions |
| `samples/.../table_sample_panel.py` | `VariantUtil.create()` for table cell data |
| `samples/.../key_value_sample_panel.py` | `VariantUtil.create()` for cell values |
| `samples/.../handler_button_sample_panel.py` | `VariantUtil.create()` for handler arguments |
| `samples/.../dashboard_sample_panel.py` | `VariantUtil.create()` for portfolio data |

### DataContainer consumers (import `DataContainer` or subclasses)

| File | Usage |
|------|-------|
| `ui/control/tree_table_control.py` | `data: list[DataContainer]` field type |
| `samples/.../tree_table_sample_panel.py` | `TreeContainer`, `TextContainer`, `NumericContainer` |
| `samples/.../dashboard_sample_panel.py` | `TreeContainer`, `TextContainer` |

---

## Future: Generics

A future phase will add `Generic[TPrim]` parameters following the `Predicate[TObj]` pattern in `records/predicates.py`:

```
PrimitiveVariant(Generic[TPrim])       value: TPrim  (on the base)
+-- StrVariant(PrimitiveVariant[str])
+-- IntVariant(PrimitiveVariant[int])
+-- ...

DataPrimitiveContainer(DataContainer, Generic[TPrim])   data: list[TPrim | None]
+-- TextContainer(DataPrimitiveContainer[str])
+-- NumericContainer(DataPrimitiveContainer[float])
+-- KeyContainer(DataPrimitiveContainer[KeyMixin])
+-- DateContainer(DataPrimitiveContainer[datetime.date])
```

This avoids repeating the `value`/`data` field on each leaf class and enables generic utilities that operate on `PrimitiveVariant[T]` or `DataPrimitiveContainer[T]`.

---

## Verification

```bash
# Variant unit tests (23 tests)
cd "<PROJECT_ROOT>" && PYTHONPATH="<PROJECT_ROOT>/runtime;<PROJECT_ROOT>/samples" \
  .venv/Scripts/python -m pytest runtime/tests/cl/runtime/records/variant/test_variant.py -vvv

# Existing UI control event tests (verify consumer imports)
cd "<PROJECT_ROOT>" && PYTHONPATH="<PROJECT_ROOT>/runtime;<PROJECT_ROOT>/samples" \
  .venv/Scripts/python -m pytest runtime/tests/cl/runtime/ui/test_control_events.py -vvv

# Regenerate TypeInfo.csv (reflects new module paths)
init_type_info.cmd

# Full test suite
cd "<PROJECT_ROOT>" && PYTHONPATH="<PROJECT_ROOT>/runtime;<PROJECT_ROOT>/samples" \
  .venv/Scripts/python -m pytest runtime/tests/ -vvv -W ignore::pytest.PytestRemovedIn9Warning
```

---

## Test Coverage

23 tests in `tests/cl/runtime/records/variant/test_variant.py`:

| Test | Description |
|------|-------------|
| `test_variant_hierarchy` | `issubclass` checks for all Variant and DataContainer relationships |
| `test_factory_str` | String wraps to `StrVariant` |
| `test_factory_int` | Integer wraps to `IntVariant` |
| `test_factory_bool` | Boolean wraps to `BoolVariant` (not `IntVariant`) |
| `test_factory_float` | Float wraps to `FloatVariant` |
| `test_factory_datetime` | `datetime.datetime` wraps to `DateTimeVariant` (not `DateVariant`) |
| `test_factory_date` | `datetime.date` wraps to `DateVariant` |
| `test_factory_time` | `datetime.time` wraps to `TimeVariant` |
| `test_factory_list` | List wraps recursively to `ListVariant` |
| `test_factory_tuple` | Tuple wraps recursively to `ListVariant` |
| `test_factory_key` | `KeyMixin` wraps to `KeyVariant` |
| `test_factory_data` | `DataclassMixin` wraps to `DataVariant` |
| `test_factory_unknown_fallback` | Unknown type falls back to `StrVariant(value=str(...))` |
| `test_factory_passthrough` | Existing `Variant` passes through unchanged |
| `test_factory_metadata` | Metadata propagates through factory |
| `test_variant_build` | Build/freeze pattern works on Variant subclasses |
| `test_text_container` | `TextContainer` construction and field access |
| `test_numeric_container` | `NumericContainer` construction and field access |
| `test_tree_container` | `TreeContainer` extends `TextContainer` with `node_separator` |
| `test_key_container` | `KeyContainer` construction and field access with `KeyMixin` values |
| `test_key_container_empty` | `KeyContainer` with empty list |
| `test_date_container` | `DateContainer` construction and field access with `datetime.date` values |
| `test_date_container_empty` | `DateContainer` with empty list |
