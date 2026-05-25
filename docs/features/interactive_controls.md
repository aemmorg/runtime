# Interactive Controls Framework (`cl.runtime.ui`)

## Overview

The Interactive Controls Framework is a server-driven UI system for building dynamic web interfaces. Controls are Python dataclasses persisted as hierarchical trees in the database. The frontend renders controls and sends user interactions back to the backend via WebSocket, where an event manager dispatches updates and returns response events. This architecture keeps all business logic server-side while providing a rich, reactive user experience.

Key design principles:
- **Server-authoritative state** -- all control state lives in the database, the frontend is a thin renderer
- **Polymorphic type-safe controls** -- 95+ control types built on the RecordMixin data model
- **Event-driven updates** -- changes propagate through a typed event pipeline with parent chain notification
- **Composition over inheritance** -- containers hold child controls via attach/detach, not deep class hierarchies

## Architecture

### Control Lifecycle

```
1. Server creates control tree (PanelControl → children)
2. Controls persisted via ControlSaver (breadth-first traversal)
3. Frontend connects via WebSocket to /events/
4. Server loads control tree, creates EventManager
5. User interacts → frontend sends event JSON
6. EventManager dispatches to typed handler
7. Handler updates control state, persists, returns response events
8. Frontend applies response events to update UI
```

### Package Structure

```
runtime/cl/runtime/ui/
├── control/                          # 95+ control implementations
│   ├── control.py                    # Abstract base: Control
│   ├── control_key.py                # Unique identifier: ControlKey
│   ├── control_container.py          # Parent container: ControlContainer
│   ├── selectable_control.py         # Selection base: SelectableControl
│   ├── panel_control.py              # Grid layout container
│   ├── tab_control.py                # Tabbed container
│   ├── sidebar_control.py            # Sidebar container
│   ├── button_control.py             # Clickable button
│   ├── handler_button_control.py     # Button with server-side handler
│   ├── input_control.py              # Single-line text input
│   ├── text_area_control.py          # Multi-line text input
│   ├── checkbox_control.py           # Two-state checkbox
│   ├── slider_control.py             # Numeric range slider
│   ├── dropdown_control.py           # Single-choice dropdown
│   ├── list_control.py               # Single-choice vertical list
│   ├── checkbox_list_control.py      # Multi-choice checkbox list
│   ├── table_control.py              # Row-major data table
│   ├── tree_table_control.py         # Hierarchical data table
│   ├── tree_control.py               # Tree navigation
│   ├── label_control.py              # Read-only text label
│   ├── text_control.py               # Read-only text display
│   ├── html_control.py               # Raw HTML display (base64)
│   ├── plotly_control.py             # Plotly chart display
│   ├── script_control.py             # Monaco code editor
│   ├── diff_control.py               # Side-by-side diff viewer
│   ├── card_control.py               # Card container
│   ├── date_filter_control.py        # Date range filter with presets
│   ├── grid_control.py               # Abstract grid base for tables
│   ├── key_value_control.py          # Key-value pair display
│   ├── configs/                      # Column/button/row configuration
│   │   ├── button_config.py          # ButtonConfig (icon, type, width)
│   │   ├── column_config.py          # ColumnConfig base class
│   │   ├── text_column_config.py     # Text column formatting
│   │   ├── numeric_column_config.py  # Numeric column formatting
│   │   ├── boolean_column_config.py  # Boolean column formatting
│   │   ├── date_column_config.py     # Date column formatting
│   │   ├── datetime_column_config.py # Datetime column formatting
│   │   └── row_config.py            # Row-level configuration
│   ├── core/                         # Enums, helpers, format classes
│   │   ├── button.py                 # Button data model
│   │   ├── button_type.py            # PRIMARY, DANGER, WARNING, SUCCESS
│   │   ├── button_icon.py            # REFRESH, ADD, DELETE, ARROW_UP, ...
│   │   ├── anchor_position.py        # TOP_LEFT through BOTTOM_RIGHT (9 positions)
│   │   ├── size_scale.py             # XS, S, M, L, XL, XXL
│   │   ├── handler_parameters.py     # Route, payload, keys, arguments
│   │   ├── selection.py              # Selection state model
│   │   ├── highlighted_area.py       # Cell highlighting model
│   │   ├── text_filter.py            # Text filter model
│   │   ├── data_type.py              # Data type enumeration
│   │   └── formats/                  # Display format classes
│   │       ├── boolean_format.py
│   │       ├── date_time_format.py   # DISTANCE, DEFAULT, etc.
│   │       └── numeric_format.py
│   └── exceptions/
│       └── control_exceptions.py     # ChildNotFoundError, etc.
├── event/                            # Event system
│   ├── ui_event.py                   # Abstract base: UiEvent
│   ├── value_update_event.py         # Single field value change
│   ├── partial_value_update_event.py # Indexed element change
│   ├── control_update_event.py       # Full control replacement
│   ├── layout_update_event.py        # Child add/remove notification
│   ├── runtime_error_event.py        # Uncaught backend exception
│   ├── user_error_event.py           # Validation error
│   ├── ui_event_handler.py           # Abstract handler base
│   ├── value_update_event_handler.py # Handles ValueUpdateEvent
│   ├── partial_value_update_event_handler.py # Handles PartialValueUpdateEvent
│   └── event_manager.py              # Central dispatcher
├── resolver/                         # Target resolution for events
│   ├── target_resolver.py            # Abstract base: TargetResolver
│   ├── control_target_resolver.py    # Resolves Control targets (viewer_name set)
│   └── record_target_resolver.py     # Resolves InteractiveMixin record targets
└── storage/                          # Persistence layer
    ├── control_manager.py            # High-level load/save/reset
    ├── control_saver.py              # Breadth-first tree persist
    └── control_loader.py             # Tree and path-based loading
```

Typed data containers (`DataContainer`, `TextContainer`, `NumericContainer`, `TreeContainer`, `KeyContainer`, `DateContainer`) live in `cl/runtime/records/variant/`, not under `ui/control/`. See [variants-and-data-containers.md](variants-and-data-containers.md) for the full hierarchy and usage.

### WebSocket Endpoint

```
runtime/cl/runtime/routers/ui_events/
├── ui_events_router.py               # /events/ WebSocket endpoint
└── connection_manager.py             # Singleton connection tracking
```

### Sample Implementations

```
samples/cl/samples/controls/
├── control_builder.py                # Factory with 20+ view methods
├── control_view_panel.py             # Base sample panel
└── panels/                           # 28 sample panels
    ├── button_sample_panel.py
    ├── text_sample_panel.py
    ├── table_sample_panel.py
    ├── ...
```

---

## Control Hierarchy

### Inheritance Tree

```
Control (abstract base, extends ControlKey + RecordMixin)
│
├── ControlContainer (abstract, manages child controls)
│   ├── PanelControl         -- Grid layout with rows/columns
│   ├── TabControl           -- Tabbed panel container
│   ├── SidebarControl       -- Vertical sidebar layout
│   └── KeyValueControl      -- Key-value pair container
│
├── GridControl (abstract, row-major data grid)
│   └── TableControl         -- Data table with sorting/filtering
│
├── TreeTableControl         -- Hierarchical column-oriented table
│
├── SelectableControl (abstract, single/multi selection)
│   ├── DropdownControl      -- Dropdown selector
│   ├── ListControl          -- Vertical list selector
│   ├── CheckboxListControl  -- Multi-select checkbox list
│   └── ChoiceListControl    -- Choice list selector
│
└── Leaf Controls (no children)
    ├── ButtonControl        -- Clickable button
    │   └── HandlerButtonControl -- Button with server-side handler
    ├── CheckboxControl      -- Two-state checkbox
    ├── InputControl         -- Single-line text input
    │   └── TextAreaControl  -- Multi-line text input
    ├── SliderControl        -- Range slider
    ├── TextControl          -- Read-only text
    │   └── LabelControl     -- Styled label
    ├── HtmlControl          -- Raw HTML (base64)
    │   └── PlotlyControl    -- Plotly chart
    ├── ScriptControl        -- Code editor (Monaco)
    ├── DiffControl          -- Diff viewer
    ├── CardControl          -- Card with content elements
    ├── TreeControl          -- Tree navigation
    └── DateFilterControl    -- Date range filter
```

### Control Identification: `ControlKey`

Every control is uniquely identified by a `ControlKey` with three fields:

| Field | Type | Description |
|-------|------|-------------|
| `view_for` | `KeyMixin` | Key of the record for which the control is displayed |
| `view_name` | `str` | Name of the view using this control |
| `control_path` | `str` | Dot-delimited path in hierarchy (e.g. `root.panel.button`) |

The root control always has `control_path = "root"`. Children derive their path from the parent: `parent.control_path + "." + child_name`.

---

## Base Control Class

**File:** `runtime/cl/runtime/ui/control/control.py`

```python
@dataclass(slots=True, kw_only=True, eq=False)
class Control(ControlKey, RecordMixin, ABC):
    parent_key: ControlKey | None = None
    label: str | None = None
    style: str | None = None
    hidden: bool = False
    enabled: bool = True
    collapsible: bool | None = False
    _parent: Optional[Control] = None       # Runtime only, not persisted
```

### Core Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `get_control_type()` | `str` | Abstract. Returns type discriminator for frontend rendering. |
| `get_key()` | `ControlKey` | Returns this control's unique key. |
| `get_children()` | `list[Control]` | Returns child controls (empty for leaf controls). |
| `set_parent(parent)` | `None` | Sets `_parent` reference for event propagation. |
| `update_control(**kwargs)` | `list[UiEvent]` | Batch-updates multiple attributes. Returns `ControlUpdateEvent`. |
| `update_value(key, value)` | `list[UiEvent]` | Updates single attribute. Returns `ValueUpdateEvent` + `on_change` events. |
| `update_partial_value(key, value, index)` | `list[UiEvent]` | Updates element in collection. Returns `PartialValueUpdateEvent` + `on_change` events. |
| `on_change(control_path, key, value)` | `list[UiEvent]` | Callback when attribute changes. Propagates to parent. Override for custom logic. |

### Update Flow

```
update_value(key="pressed", value=True)
  1. Validate attribute exists via type hints
  2. Deserialize value to correct type
  3. Set attribute on control object
  4. Persist via DataSource.replace_one()
  5. Create ValueUpdateEvent(control_path, key, value)
  6. Call self.on_change(control_path, key, value)
     └── on_change propagates to _parent.on_change()
  7. Return [ValueUpdateEvent, ...on_change_events]
```

---

## Container Controls

### `ControlContainer`

**File:** `runtime/cl/runtime/ui/control/control_container.py`

Extends `Control` with child management:

```python
@dataclass(slots=True, kw_only=True, eq=False)
class ControlContainer(Control, ABC):
    control_keys: list[ControlKey] = []          # Persisted child keys
    _controls: list[Control] | None = []         # Runtime child instances
    _added_controls: list[Control] | None = []   # Newly added (pending save)
    _removed_controls: list[str] | None = []     # Marked for removal
```

| Method | Returns | Description |
|--------|---------|-------------|
| `attach_control(control)` | `None` | Adds child, sets its path/key/parent references. |
| `remove_control(control_path)` | `None` | Marks child (and descendants) for removal. |
| `load_child(control_path, cast_to)` | `TControl` | Loads child from storage by relative path. |
| `update_layout()` | `list[UiEvent]` | Persists add/remove changes. Returns `LayoutUpdateEvent`. |
| `init_content()` | `None` | Abstract. Populates container with initial children. |

### `PanelControl`

Grid layout container with configurable dimensions:

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `col_count` | `int \| None` | `None` | Number of columns |
| `row_count` | `int \| None` | `None` | Number of rows |
| `row_height` | `str \| None` | `None` | CSS row height |
| `col_width` | `str \| None` | `None` | CSS column width |
| `bordered` | `bool` | `False` | Show border |
| `show_grid` | `bool` | `False` | Show grid lines |
| `padding` | `str \| None` | `None` | CSS padding |
| `gap` | `str \| None` | `None` | CSS gap between cells |

### `TabControl`

Tabbed container:

| Attribute | Type | Description |
|-----------|------|-------------|
| `tab_headers` | `list[str]` | Tab labels |
| `selected_tab` | `int` | Currently active tab index |

Method: `create_new_tab(tab_name, control: PanelControl) -> list[UiEvent]` -- adds a tab with its panel content. Returns UI events for `tab_headers` update. Ignore return value during `init_content`; collect events in `on_change` and call `update_layout()` after.

### `SidebarControl`

Vertical sidebar:

| Attribute | Type | Description |
|-----------|------|-------------|
| `show_dividers` | `bool` | Show dividers between items |
| `gap` | `str \| None` | CSS gap between items |

---

## Event System

### Event Types

All events inherit from `UiEvent` which carries `key: str`.

| Event Class | Fields | When Emitted |
|-------------|--------|--------------|
| `ValueUpdateEvent` | `key`, `value` | Single attribute changed via `update_value()` |
| `PartialValueUpdateEvent` | `key`, `value`, `index` | Collection element changed via `update_partial_value()` |
| `ControlUpdateEvent` | `control` (full object) | Multiple attributes changed via `update_control()` |
| `LayoutUpdateEvent` | `removed_controls`, `added_controls` | Children added/removed via `update_layout()` |
| `RuntimeErrorEvent` | `error` | Uncaught exception during event processing |
| `UserErrorEvent` | `error` | Validation failure from user action |

### Event Flow (Frontend → Backend → Frontend)

```
┌──────────┐    WebSocket JSON     ┌──────────────┐
│ Frontend │ ─────────────────────→│  /events/     │
│          │                       │  (WebSocket)  │
│          │                       └──────┬───────┘
│          │                              │
│          │                     ┌────────▼────────┐
│          │                     │  EventManager   │
│          │                     │  .dispatch()    │
│          │                     └────────┬────────┘
│          │                              │
│          │                     ┌────────▼────────┐
│          │                     │  Event Handler  │
│          │                     │  (typed)        │
│          │                     └────────┬────────┘
│          │                              │
│          │                     ┌────────▼────────┐
│          │                     │  Control        │
│          │                     │  .update_*()    │
│          │                     └────────┬────────┘
│          │                              │
│          │                     ┌────────▼────────┐
│          │                     │  on_change()    │
│          │                     │  propagation    │
│          │                     └────────┬────────┘
│          │                              │
│          │   list[UiEvent] JSON    │
│          │ ←────────────────────────────┘
└──────────┘
```

### Inbound Event JSON Format

```json
{
  "_t": "ValueUpdateEvent",
  "ControlPath": "root.panel.button",
  "Key": "Pressed",
  "Value": true
}
```

```json
{
  "_t": "PartialValueUpdateEvent",
  "ControlPath": "root.panel.table",
  "Key": "Data",
  "Index": "1",
  "Value": {"_t": "StrVariant", "Value": "Changed"}
}
```

The `_t` field is the type discriminator. `Key` uses PascalCase (converted to snake_case by the handler). `ControlPath` identifies the target control in the tree.

### EventManager

**File:** `runtime/cl/runtime/ui/event/event_manager.py`

Central dispatcher that:
1. Receives raw event dict from WebSocket
2. Ignores keep-alive messages
3. Uses the configured `TargetResolver` to locate the target (Control or InteractiveMixin record) for the event's `Key`
4. Deserializes event using `BootstrapSerializers.FOR_UI_EVENTS`
5. Routes to the correct handler from the registry (keyed by event type name)
6. Returns response events (wraps `UserError` in `UserErrorEvent`, any other exception in `RuntimeErrorEvent`)

Handler registry (`SUPPORTED_EVENT_HANDLERS` keyed by `typename(EventClass)`):

```python
SUPPORTED_EVENT_HANDLERS = {
    typename(ValueUpdateEvent): ValueUpdateEventHandler,
    typename(PartialValueUpdateEvent): PartialValueUpdateEventHandler,
}
```

### Target Resolvers

`EventManager` is constructed with a `TargetResolver` that abstracts how the event target is found:

| Resolver | When Used | Loads |
|----------|-----------|-------|
| `ControlTargetResolver(key, viewer_name)` | `viewer_name` is set (Control tree events) | Target `Control` (with parent chain) via `ControlLoader.load_by_path` |
| `RecordTargetResolver(key, type_name)` | `viewer_name` is empty (direct record events) | Target `InteractiveMixin` record by key |

### Event Handlers

**ValueUpdateEventHandler:**
1. Converts `Key` from PascalCase to snake_case
2. Resolves field type hint from control class
3. Deserializes `Value` to the correct Python type
4. Calls `control.update_value(key, deserialized_value)`

**PartialValueUpdateEventHandler:**
1. Same key/type resolution as above
2. Additionally resolves nested type hint from `Index` path
3. Calls `control.update_partial_value(key, value, index)`

---

## Persistence Layer

### Control Identification

Controls are stored as individual records keyed by `ControlKey(view_for, view_name, control_path)`. Parent-child relationships are maintained via:
- `parent_key` on each child control (points to parent's ControlKey)
- `control_keys` on each ControlContainer (list of child ControlKeys)

### ControlSaver

**File:** `runtime/cl/runtime/ui/storage/control_saver.py`

Saves a control tree using breadth-first traversal. Each control is persisted as a separate record via `DataSource.replace_one()`. Children are discovered via `get_children()`.

### ControlLoader

**File:** `runtime/cl/runtime/ui/storage/control_loader.py`

Two loading modes:
1. **Full tree load** (`load()`) -- recursively loads root + all descendants
2. **Path-based load** (`load_by_path(control_path, parents=True)`) -- loads a single control with its parent chain. Used by EventManager to reconstruct the `on_change` propagation path.

Path resolution handles indexed items (e.g., `root.list.3`) by resolving the index against the parent DataContainer.

### ControlManager

**File:** `runtime/cl/runtime/ui/storage/control_manager.py`

High-level orchestrator:

| Method | Description |
|--------|-------------|
| `load()` | Load full control tree |
| `load_one()` | Load single control by key |
| `save()` | Persist control tree |
| `remove(selected_controls)` | Delete specific controls |
| `reset(**kwargs)` | Delete and recreate control tree |

---

## WebSocket Endpoint

**File:** `runtime/cl/runtime/routers/ui_events/ui_events_router.py`

**URL:** `/events/`

**Query Parameters:**

| Parameter | Description |
|-----------|-------------|
| `key` | View entity identifier |
| `type` | Type name of entity |
| `viewer_name` | View name |

**Connection Flow:**
1. Accept WebSocket connection
2. Choose the resolver based on `viewer_name` (each resolver owns its own key deserialization):
   - `viewer_name` set → `ControlTargetResolver(key=key, type_name=type, viewer_name=viewer_name)`
   - `viewer_name` empty → `RecordTargetResolver(key=key, type_name=type)` (empty `key` = not-yet-created record)
3. Create `EventManager(resolver=resolver)`
4. Enter message loop:
   - Receive text message
   - Dispatch via `event_manager.dispatch(event_dict)`
   - Serialize response events
   - Send JSON response
5. Handle disconnect/errors gracefully

**ConnectionManager** (singleton) tracks active connections per key, enabling broadcast to multiple clients viewing the same control tree.

---

## Control Configuration

### Button Configuration

```python
@dataclass(slots=True, kw_only=True)
class ButtonConfig(DataclassMixin):
    help: str | None = None                          # Tooltip text
    icon: ButtonIcon | None = None                   # Icon enum value
    width: str | None = "content"                    # CSS width
    type: ButtonType | None = ButtonType.PRIMARY     # Semantic style
    position: AnchorPosition | None = AnchorPosition.TOP_LEFT
```

### Handler Parameters

```python
@dataclass(slots=True, kw_only=True)
class HandlerParameters(DataclassMixin):
    route: str                    # API route to invoke
    payload: dict | None          # Request payload
    keys: list[str] | None       # Record keys for the handler
    arguments: dict | None        # Method arguments
```

### Column Configurations

| Config Class | Purpose | Key Attributes |
|--------------|---------|----------------|
| `ColumnConfig` | Base class | `label`, `hidden`, `editable`, `width`, `style` |
| `TextColumnConfig` | Text columns | `max_length`, `wrap` |
| `NumericColumnConfig` | Number columns | `format: NumericFormat`, `precision` |
| `BooleanColumnConfig` | Boolean columns | `format: BooleanFormat` |
| `DateColumnConfig` | Date columns | `format: DateTimeFormat` |
| `DatetimeColumnConfig` | Datetime columns | `format: DateTimeFormat` |

### Style Enums

| Enum | Values |
|------|--------|
| `ButtonType` | `PRIMARY`, `DANGER`, `WARNING`, `SUCCESS` |
| `ButtonIcon` | `REFRESH`, `SUCCESS`, `ERROR`, `INFO`, `BELL`, `ADD`, `DELETE`, `ARROW_UP`, `ARROW_DOWN`, `THUMB_UP`, `THUMB_DOWN` |
| `AnchorPosition` | `TOP_LEFT`, `TOP_CENTER`, `TOP_RIGHT`, `CENTER_LEFT`, `CENTER`, `CENTER_RIGHT`, `BOTTOM_LEFT`, `BOTTOM_CENTER`, `BOTTOM_RIGHT` |
| `SizeScale` | `XS`, `S`, `M`, `L`, `XL`, `XXL` |
| `DateTimeFormat` | `DEFAULT`, `DISTANCE` |

---

## Data Controls

### TableControl

**File:** `runtime/cl/runtime/ui/control/table_control.py`

Extends `GridControl` with row-major flattened data storage.

| Attribute | Type | Description |
|-----------|------|-------------|
| `data` | `list[Variant]` | Flattened row-major cell data |
| `col_names` | `list[str]` | Column headers |
| `row_names` | `list[str]` | Row identifiers |
| `selected_row` | `int \| None` | Currently selected row index |
| `cell_styles` | `dict` | Per-cell CSS styling |
| `col_filters` | `list` | Active column filters |
| `col_config` | `list[ColumnConfig]` | Per-column configuration |
| `row_config` | `list[RowConfig]` | Per-row configuration |
| `multi_header_separator` | `str` | Separator for multi-level headers |

Data access methods:
- `get_row_data(row_index)` / `get_row_data(row_name)` -- yields cells in a row
- `get_column_data(col_index)` / `get_column_data(col_name)` -- yields cells in a column
- `get_selected_row_data()` -- yields cells in the selected row

### TreeControl

**File:** `runtime/cl/runtime/ui/control/tree_control.py`

Hierarchical tree navigation:

| Attribute | Type | Description |
|-----------|------|-------------|
| `child_nodes` | `list[TreeControlNode]` | Root-level tree nodes |
| `selected_node_path` | `str \| None` | Path to selected node |
| `expanded_nodes` | `list[str]` | Paths of expanded nodes |

Node paths use `"."` as separator (e.g. `"root.child.grandchild"`).

### TreeTableControl

**File:** `runtime/cl/runtime/ui/control/tree_table_control.py`

Column-oriented table with tree-structured rows. Unlike `TableControl` (row-major `Variant` cells), `TreeTableControl` stores data column-by-column using typed `DataContainer` subclasses. The first column is typically a `TreeContainer` whose separator-delimited paths define the row hierarchy.

| Attribute | Type | Description |
|-----------|------|-------------|
| `columns` | `list[ColumnConfig]` | Column configurations (parallel to `data`) |
| `data` | `list[DataContainer]` | Column data containers (parallel to `columns`) |
| `selected_row` | `int \| None` | Currently selected row index |
| `expand_all` | `bool` | When True all tree rows are expanded on initial render (default False) |
| `multi_header_separator` | `str \| None` | Splits column labels into grouped multi-level headers (e.g. `"."` turns `"Metrics.CVA"` into a "Metrics" group with "CVA" sub-column) |

#### Data Containers

All containers extend `DataContainer` (abstract base in `cl/runtime/records/variant/data_container.py`):

| Container | `data` Type | Description |
|-----------|-------------|-------------|
| `TextContainer` | `list[str \| None]` | String values, one per row |
| `NumericContainer` | `list[float \| None]` | Numeric values, one per row |
| `TreeContainer` | `list[str \| None]` | Separator-delimited paths defining tree hierarchy. Has `node_separator: str` attribute |
| `KeyContainer` | `list[KeyMixin \| None]` | Record key values, one per row |
| `DateContainer` | `list[datetime.date \| None]` | Date values, one per row |

See [variants-and-data-containers.md](variants-and-data-containers.md) for the full container hierarchy.

`columns[i]` configures `data[i]` — the two lists are parallel. Parent nodes in `TreeContainer.data` must appear before their children.

#### Multi-Level Column Headers

When `multi_header_separator` is set, column labels containing the separator are split into grouped headers. For example, with `multi_header_separator="."`:

```
ColumnConfig(label="Metrics.CVA"), ColumnConfig(label="Metrics.DVA")
```

renders as a "Metrics" group header spanning two sub-columns "CVA" and "DVA".

**Important:** Use a different character for `TreeContainer.node_separator` than for `multi_header_separator` to avoid collision (e.g. `node_separator="~"` with `multi_header_separator="."`).

---

## Implementing Custom Controls

### Creating a Panel with Business Logic

Override `init_content()` to build the control tree and `on_change()` to handle interactions:

```python
@dataclass(slots=True, kw_only=True, eq=False)
class MyPanel(PanelControl):
    def init_content(self) -> None:
        # Create child controls
        button = ButtonControl(
            control_path="action_btn",
            label="Run Analysis",
            config=ButtonConfig(icon=ButtonIcon.REFRESH, type=ButtonType.PRIMARY),
        )
        self.attach_control(button)

        output = LabelControl(
            control_path="output_label",
            label="Result",
            value="Click button to start",
        )
        self.attach_control(output)

    def on_change(self, control_path: str, key: str, value: str) -> list[UiEvent]:
        events = []
        if control_path.endswith("action_btn") and key == "pressed":
            # Business logic here
            result = run_analysis()
            label = self.load_child("output_label", LabelControl)
            events.extend(label.update_value("value", result))
        return events
```

### Pattern: Button Click → Chart Update

From `ButtonSamplePanel`:

```python
def on_change(self, control_path, key, value):
    events = []
    if control_path.endswith("button") and key == "pressed":
        chart = self.load_child("chart", PlotlyControl)
        fig = generate_chart_data()
        content = PlotlyControl.encode_plot(fig, use_app_theme=True)
        events.extend(chart.update_value("content", content))
    return events
```

### Pattern: Text Input → Live Statistics

From `TextSamplePanel`:

```python
def on_change(self, control_path, key, value):
    events = []
    if control_path.endswith("text_area") and key == "value":
        stats_label = self.load_child("stats", LabelControl)
        word_count = len(value.split())
        events.extend(stats_label.update_value("value", f"Words: {word_count}"))
    return events
```

### Pattern: Dynamic Tab Addition

From `TabSamplePanel` — adding a new tab to an existing `TabControl` at runtime:

```python
def on_change(self, key, field, value, index=None):
    events = []
    if key.endswith("add_new_tab") and field == "pressed":
        tab_control = self.load_child("tabs", TabControl)
        new_panel = PanelControl(control_path="new_panel")
        events += tab_control.create_new_tab("New Tab", new_panel)
        # ... populate new_panel with child controls ...
        events += tab_control.update_layout()
    return events
```

`create_new_tab()` returns `list[UiEvent]` with a `ValueUpdateEvent` for `tab_headers`.
During initial creation (in `init_content`) the return value can be ignored.
When adding to an existing control, collect the events and call `update_layout()` to persist the new children.

### Pattern: Dynamic Layout Changes

```python
def on_change(self, control_path, key, value):
    events = []
    if control_path.endswith("add_btn") and key == "pressed":
        new_control = LabelControl(control_path="dynamic_label", value="New item")
        self.attach_control(new_control)
        events.extend(self.update_layout())  # Returns LayoutUpdateEvent
    return events
```

---

## on_change Propagation

The `on_change` callback is the primary extensibility point. When a control's value changes:

1. The control itself has `on_change()` called
2. Default implementation propagates to `_parent.on_change()` with the same arguments
3. Any control in the parent chain can intercept and respond
4. Each handler returns `list[UiEvent]` which accumulates upward

```
ButtonControl.update_value("pressed", True)
  → ButtonControl.on_change("root.panel.button", "pressed", "True")
    → PanelControl.on_change("root.panel.button", "pressed", "True")   ← override here
      → Root.on_change(...)  (default: no-op at root)
```

This enables parent panels to react to any descendant change without the child knowing about the parent's logic.

---

## Sample Panels

The `samples/cl/samples/controls/panels/` directory contains 28 sample panels demonstrating each control type:

| Sample Panel | Controls Demonstrated |
|---|---|
| `ButtonSamplePanel` | ButtonControl, ButtonConfig, PlotlyControl, button click → chart update |
| `TextSamplePanel` | InputControl, TextAreaControl, LabelControl, ScriptControl, live text statistics |
| `TableSamplePanel` | TableControl, column configs (Datetime, Numeric, Boolean), cell styles, filters |
| `CheckboxSamplePanel` | CheckboxControl, checkbox state handling |
| `DropdownSamplePanel` | DropdownControl, DropdownControlItem, selection handling |
| `SliderSamplePanel` | SliderControl, range binding |
| `TreeSamplePanel` | TreeControl, TreeControlNode, node selection |
| `TabSamplePanel` | TabControl, tab creation, tab switching |
| `DiffSamplePanel` | DiffControl, side-by-side diff display |
| `CardSamplePanel` | CardControl, CardContent variants |
| `ListSamplePanel` | ListControl, ListControlItem |
| `CheckboxListSamplePanel` | CheckboxListControl, multi-selection |
| `DateFilterSamplePanel` | DateFilterControl, presets, date range |
| `ScriptSamplePanel` | ScriptControl, code editing |
| `SidebarSamplePanel` | SidebarControl, vertical layout |
| `HandlerButtonSamplePanel` | HandlerButtonControl, server-side handler invocation |

The `ControlBuilder` class in `control_builder.py` provides factory methods (e.g. `view_button()`, `view_table()`) that create `ControlView` instances pointing to these sample panels.

---

## Test Coverage

Test files in `runtime/tests/`:

| Test File | What It Tests |
|-----------|---------------|
| `test_control_events.py` | ValueUpdateEvent, PartialValueUpdateEvent, ControlUpdateEvent creation and serialization |
| `test_event_manager.py` | EventManager dispatch flow, error handling, keep-alive message filtering |
| `test_control_storages.py` | ControlSaver/ControlLoader round-trip, tree persistence |
| `test_ui_events_serialization.py` | Event JSON serialization/deserialization fidelity |

Test pattern:
1. Create a test panel with known child controls
2. Save via `ControlSaver`
3. Dispatch events via `EventManager`
4. Assert correct event types, control paths, and updated values in response

---

## Key Design Decisions

1. **Server-side state ownership** -- Controls are persisted in the database, not held in frontend state. This ensures consistency across multiple clients and enables server-side business logic without client round-trips.

2. **Breadth-first persistence** -- Control trees are saved level-by-level, each node as an independent record. This allows loading individual controls by path without loading the entire tree.

3. **Type-discriminated serialization** -- The `_t` field in JSON enables polymorphic deserialization. The backend resolves `_t` to the correct Python class via `BootstrapSerializers`.

4. **Parent chain loading for events** -- When processing an event, only the target control and its ancestors are loaded (not the full tree). This minimizes database reads while enabling `on_change` propagation.

5. **Immutable build pattern** -- Controls follow the project's `BuilderMixin` pattern: construct with fields, call `.build()` to freeze.

6. **PascalCase ↔ snake_case bridge** -- Frontend sends PascalCase field names (`Key: "Pressed"`), handlers convert to Python snake_case (`pressed`). This maintains JavaScript and Python naming conventions without coupling.
