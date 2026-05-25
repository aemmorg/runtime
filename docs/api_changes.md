## v2.4.0

### Summary

- **Breaking Change:** Removed `User` field from `UiAppStateKey`, `UiTypeStateKey`, and `UiTypeLayoutKey`. The keys are no longer user-scoped — UI app state, type state, and type layout are now identified without a `UserKey` reference.
- **Breaking Change:** `UiAppStateKey` gained a new key field `Id: str` replacing the removed `User` field. When a `UiAppState` record is saved without an `Id`, the `__init` builder hook populates `Id` with the literal `"default"` so the record is still addressable.

### Affected types and keys

| Type | Before | After |
|---|---|---|
| `UiAppStateKey` | `{ User: UserKey }` | `{ Id: string }` |
| `UiTypeStateKey` | `{ Type: TypeDeclKey, User: UserKey }` | `{ Type: TypeDeclKey }` |
| `UiTypeLayoutKey` | `{ Type: TypeDeclKey, User: UserKey }` | `{ Type: TypeDeclKey }` |

The record bodies (`UiAppState`, `UiTypeState`, `UiTypeLayout`) lose the inherited `User` field accordingly; the rest of the record schema is unchanged.

### Affected routes

- `POST /storage/save` — payloads for `_t = UiAppState | UiTypeState | UiTypeLayout` must omit the `User` field. `UiAppState` payloads should send `Id` (any string); omitting `Id` is accepted and stored as `"default"`.
- `POST /storage/load`, `POST /storage/select`, `POST /storage/delete` — `KeyRequestItem.Key` for these three key types is now the new delimited key form (no `User` token):
  - `UiAppStateKey`: `"<id>"` (e.g. `"default"`)
  - `UiTypeStateKey` / `UiTypeLayoutKey`: `"<module>;<type_name>"` (e.g. `"cl;UiAppState"`)
- `UiAppState.get_global_app_state()` / `UiAppState.get_current_user_app_theme()` no longer look up state by `UserKey`; they read a single `UiAppStateKey` derived from the new `Id` field.

### Migration Impact

- **Frontend (BREAKING):** Drop the `User` field from any `UiAppState`, `UiTypeState`, or `UiTypeLayout` payload you POST to `/storage/save`. Update key construction for `/storage/load`, `/storage/select`, and `/storage/delete` to use the new key shapes above (`Id` only for `UiAppStateKey`; `Type` only for `UiTypeStateKey` / `UiTypeLayoutKey`).
- **Backend callers:** Any Python code that constructed `UiAppStateKey(user=...)`, `UiTypeStateKey(type_=..., user=...)`, or `UiTypeLayoutKey(type_=..., user=...)` must be updated to drop the `user=` argument; `UiAppStateKey` now takes `id=...` instead. The `get_key()` implementations of the three records and the `LoadResponse._get_default_ui_type_state` helper have already been updated.
- **Stored data:** Documents persisted under v2.3.x carry a `User` field on these records; the field is ignored on load and dropped on the next write. Existing rows keyed by `User` will not collide with the new `Id`-based keys, but they will no longer be reachable through the new key shape — plan a one-time migration if continuity is required.
- Regenerate `resources/bootstrap/TypeInfo.csv` via `init_type_info.cmd` so the schema and key field changes propagate to clients.

---

## v2.3.0

### Summary

- **Breaking Change:** `Type:'DataService' Method:'RunDataEnvs'` response changed from a JSON array of `DataEnvItem` to `DataEnvsResponse` — an object `{ DataEnvItems: [...], DefaultEnv: string | null }`. The element shape inside `DataEnvItems` is unchanged from v2.2.0. `DefaultEnv` is the `Name` of the alphabetically first root, or `null` when empty.
- **Breaking Change:** Removed `UiAppState.active_data_env` (`ActiveDataEnv` on the wire). The initial active environment is now sourced from `DataEnvsResponse.default_env` (`DefaultEnv`) returned by `DataService.run_data_envs()`.

### Migration Impact

- **Frontend (BREAKING):** Read the tree from `response.DataEnvItems` and use `response.DefaultEnv` as the initial active env. Stop reading `ActiveDataEnv` from `UiAppState` — the field is no longer emitted.
- **Backend callers:** `DataService.run_data_envs()` now returns `DataEnvsResponse` — read `result.data_env_items` / `result.default_env`. Any code that read or wrote `UiAppState.active_data_env` must be removed.
- **Stored data:** `UiAppState` documents persisted under v2.2.0 may contain an `ActiveDataEnv` field; it is ignored on load and can be dropped during the next write.
- Regenerate `resources/bootstrap/TypeInfo.csv` via `init_type_info.cmd` to register the new `DataEnvsResponse` type and the updated `UiAppState` schema.

---

## v2.2.3

### Summary

- **Added:** `AppFeatures.bi_tools` flag — controls visibility of Business Intelligence features (charting, pivot grids, dashboard building). Default `True`.
- **Added:** `AppFeatures.display_local_time` flag — enables the Display Local Time toggle in the UI so datetime fields render in browser/user/tenant timezone with UTC-conversion on submit. Default `None`.
- **Added:** Companion `AppFeatureSettings` fields `app_feature_bi_tools` (default `True`) and `app_feature_display_local_time` (default `None`).
- **Changed:** `SettingsResponse.get_response()` now also wires `bi_tools` and `display_local_time` from `AppFeatureSettings.instance()`.

### AppFeatures additions

- `bi_tools: bool | None = True` — when `True`, BI controls (Plotly charts, pivot grid, dashboard builder) are available; when `False` or `None`, they are hidden.
- `display_local_time: bool | None = None` — when `True`, the UI offers per-user control to render datetime fields in local time (browser timezone, or the user/tenant timezone if set) and to convert local input back to UTC before submission. When `False` or `None`, datetime fields show server-side UTC values verbatim.

### AppFeatureSettings additions

| Settings field | Maps to `AppFeatures` field | Default |
|---|---|---|
| `app_feature_bi_tools` | `bi_tools` | `True` |
| `app_feature_display_local_time` | `display_local_time` | `None` |

### Migration Impact

- No breaking changes to the wire contract. Both new fields are optional and absent in older responses.
- Frontend `AppFeaturesModel` should add `BiTools?: boolean | null` and `DisplayLocalTime?: boolean | null` to consume the new flags from the `/settings` response.
- Deployments that want non-default values should set them via `CL_APP_FEATURE_BI_TOOLS` / `CL_APP_FEATURE_DISPLAY_LOCAL_TIME` env vars or `app_feature_bi_tools` / `app_feature_display_local_time` keys in `settings.yaml`.

---

## v2.2.2

### Summary

- **Fixed:** OIDC callback and logout redirect URLs no longer concatenate path segments into the previous page's path. The previous f-string formulas assumed `frontend_referer` ended at the site root (e.g. `https://app.example.com/`), but real browsers send `Referer:` of the page that initiated the action (e.g. `https://app.example.com/login` or `https://app.example.com/dashboard`), which produced broken artifacts like `loginlogin/callback` for OIDC providers such as Entra ID. URLs are now built via `urlparse` / `urlunparse`, mutating the path component explicitly and dropping any query / fragment from the source referer.

### Affected routes

- `GET /auth/{provider}/callback` — redirect `Location` header changed from `{referer}login/callback?provider_id=...` to `{referer_path}/callback?provider_id=...` (built on the referer's host + path with `/callback` appended).
- OIDC `redirect_uri` sent to the provider during `POST /auth/{provider}/login-redirect` changed from `{frontend_referer}login/callback` to `{frontend_referer_path}/callback`.
- Provider logout redirect (`POST /auth/{provider}/logout`) changed from `{frontend_referer}logout/callback` to `{frontend_referer_path}/logout/callback` for the same reason.

### Migration Impact

- **Frontend:** No client-side change required if the frontend already serves the post-login callback at `/login/callback` and `Referer` points to `/login` — the resulting URL is identical to what the old buggy code produced when `referer` was the site root. Verify that the frontend routes still match the constructed URLs given your deployment's `Referer` values (note: logout callback path is now relative to the page the user logged out from, so an FE serving a fixed root-level `/logout/callback` needs to either register the new path or move logout invocation to a stable location).
- **OIDC provider configuration:** If your provider whitelists the exact `redirect_uri`, ensure the registered value matches the page actually serving login (typically `https://<host>/login/callback`). Providers configured against a root-relative `redirect_uri` that worked by accident with the old `loginlogin` artifact will need their whitelist updated.

---

## v2.2.1

### Summary

- **Added:** `AppFeatures.search_tables` flag — controls visibility of the Tables section alongside Types in the header search dropdown.
- **Added:** `AppFeatures.show_user_id` flag — controls visibility of the user ID row in the user info popup.
- **Added:** `AppFeatures.simplified_ui` flag — when `True`, the UI hides a curated set of advanced controls.
- **Added:** `AppFeatureSettings` (Dynaconf-driven settings class with `app_feature_` prefix) backing every `AppFeatures` field on the `/settings` response.
- **Changed:** `SettingsResponse.get_response()` now sources `AppFeatures` values from `AppFeatureSettings.instance()` instead of hardcoding them.

### AppFeatures additions

- `search_tables: bool | None = None` — when `True`, the header search dropdown shows the Tables section alongside Types (and Filters); when `False`, the Tables section is hidden. `None` leaves the choice to the frontend default.
- `show_user_id: bool | None = True` — when `True`, the user info popup displays the ID field; when `False`, the ID row is hidden.
- `simplified_ui: bool | None = None` — when `True`, the UI enters a simplified mode that hides a curated set of advanced controls (developer-oriented buttons and menus). When `False` or `None`, the full UI is shown.

### AppFeatureSettings (new)

A `Settings` subclass at `cl.runtime.settings.app_feature_settings.AppFeatureSettings` exposing one field per `AppFeatures` flag, prefixed with `app_feature_`. Values are read from environment variables (`CL_APP_FEATURE_*`), `.env`, or `settings.yaml` (`app_feature_*` keys), following the standard `Settings` resolution order.

| Settings field | Maps to `AppFeatures` field | Default |
|---|---|---|
| `app_feature_ai_chat` | `ai_chat` | `None` |
| `app_feature_data_env_support` | `data_env_support` | `False` |
| `app_feature_dataset_support` | `dataset_support` (fallback only) | `False` |
| `app_feature_db_tools` | `db_tools` | `True` |
| `app_feature_demo_mode` | `demo_mode` | `None` |
| `app_feature_internal_apps_support` | `internal_apps_support` | `False` |
| `app_feature_search_tables` | `search_tables` | `None` |
| `app_feature_show_user_id` | `show_user_id` | `True` |
| `app_feature_simplified_ui` | `simplified_ui` | `None` |

`dataset_support` remains dynamic when a `DataSource` is active (driven by `Db.supports_datasets`); `app_feature_dataset_support` is used as a fallback when no `DataSource` is in scope.

### SettingsResponse.get_response() rewiring

`AppFeatures` is now constructed from `AppFeatureSettings.instance()` rather than from hardcoded values. The wire shape of `SettingsResponse` is unchanged.

The deprecated top-level mirror field `dataset_support` (removed in an earlier release) is no longer passed to the constructor; it had been silently dropped by Pydantic.

### Migration Impact

- No breaking changes to the wire contract. Both new `AppFeatures` fields are optional and absent in older responses.
- Frontend `AppFeaturesModel` should add `SearchTables?: boolean | null`, `ShowUserId?: boolean | null`, and `SimplifiedUi?: boolean | null` to consume the new flags from the `/settings` response.
- Deployments that want non-default feature flag values should set them via `CL_APP_FEATURE_*` env vars or under the active environment block in `settings.yaml`. Previous hardcoded defaults (`db_tools=True`, `internal_apps_support=True`) are now `True` / `False` respectively — verify the new `internal_apps_support` default matches your deployment expectations.

---

## v2.2.0

### Summary

- **Breaking Change:** Renamed `EnvService` and its companion types to internal-app terminology (module paths and file names unchanged; only symbols rename).
- **Added:** `AuthPreprocessor` extension point — pluggable hook invoked from `activate_auth_context` before the request handler runs.
- **Added:** `DataService.run_data_envs()` returning a hierarchical `DataEnvItem` tree; companion `UiAppState.active_data_env` and `AppFeatures.data_env_support` flag.

### EnvService → AppService rename

| Old | New | Kind |
|-----|-----|------|
| `EnvService` | `AppService` | class |
| `Environments` | `InternalApps` | record |
| `EnvironmentsKey` | `InternalAppsKey` | key |
| `EnvDescriptor` | `InternalAppDescriptor` | data |
| `run_envs` | `run_internal_apps` | classmethod |
| `run_set_active_env(env_name)` | `run_set_active_internal_app(app_name)` | classmethod + arg |
| `active_env_name` / `envs` | `active_app_name` / `apps` | `InternalApps` fields |
| `env_name` / `env_kind` | `app_name` / `app_kind` | descriptor fields |
| `AppFeatures.envs_support` | `AppFeatures.internal_apps_support` | settings field |

Wire format follows the rename: discriminators `Type:'EnvService'` → `Type:'AppService'`; `Method:'RunEnvs'` → `Method:'RunInternalApps'`; `Method:'RunSetActiveEnv'` (arg `EnvName`) → `Method:'RunSetActiveInternalApp'` (arg `AppName`). Response keys `ActiveEnvName` / `Envs` / `EnvName` / `EnvKind` → `ActiveAppName` / `Apps` / `AppName` / `AppKind`. `EnvsSupport` → `InternalAppsSupport` inside `Features`. `Parent` / `Url` / `Description` unchanged. The deprecated `GET /storage/envs` route is unchanged on the wire. `PUBLIC_TYPES` updated to contain `"AppService"` in place of `"EnvService"`.

### AuthPreprocessor

- New abstract `cl.runtime.server.auth_preprocessor.AuthPreprocessor`; default `PreloadAuthPreprocessor` encapsulates the prior inline preload-if-empty logic from `auth_dependency.py`. Configured via `AuthSettings.auth_preprocessor_type` (default `"PreloadAuthPreprocessor"`).
- Hook `preprocess(*, request, websocket)` runs after `DataSource` / `EventBroker` / `CeleryQueue` contexts are pushed. No wire-format change.

### DataEnv hierarchy

- New handler `Type:'DataService' Method:'RunDataEnvs'` — returns a JSON array of `DataEnvItem` (PascalCase: `Name`, `Description`, `Server`, `ChildDataEnvs`). Children sorted alphabetically; orphans attach at root; cycles raise `RuntimeError`.
- `UiAppState` gains optional `active_data_env: str | None` (`ActiveDataEnv` on the wire).
- `AppFeatures` gains optional `data_env_support: bool | None` (`DataEnvSupport` inside `Features`).

### Migration Impact

- **Backend:** Update call sites and constructor args to the renamed forms.
- **Frontend (BREAKING for env/internal-apps screen):** Update `Type` / `Method` discriminators, PascalCase response keys, and the `EnvsSupport` → `InternalAppsSupport` settings field. Until updated, the env/internal-apps screen will not load.
- **Stored data:** `InternalApps` documents written under the old field names won't be readable — drop and let `run_internal_apps` recreate, or migrate the document keys before deploying.
- **Custom auth preprocessors:** Subclass `AuthPreprocessor`, set `AuthSettings.auth_preprocessor_type`, and ensure the subclass is discoverable via `TypeInfo.csv`.
- **`resources/bootstrap/TypeInfo.csv`:** regenerate via `init_type_info.cmd` after deploying so the catalog reflects the renamed classes, the new auth preprocessor types, `DataEnvItem`, and the new `UiAppState` field.

---

## v2.1.0

### Summary

- **Added:** Two mutability flags on `DataSpec` — `not_editable` and `not_deletable` — that do double duty: developers declare them at schema level to mark types as frozen / retention-locked, and the API layer rewrites them at request time on a per-user basis (the wire value is the union of the schema declaration and any permission deficit). Inverted-default convention: omitted flag = allowed (the common case); `True` = forbidden.
- **Removed (wire format):** Previous interim shapes — `not_creatable`, the separate `UserCanCreate` / `UserCanEdit` / `UserCanDelete` per-user fields, and the legacy `Editable` / `Deletable` runtime mirrors — are all gone. The response carries only `NotEditable` / `NotDeletable`.
- **Deprecated (declaration):** `readonly`, `editable`, `deletable` on `DataSpec`. Setting any of these on a schema declaration now emits a `DeprecationWarning` and is translated forward (`readonly=True` / `editable=False` → `not_editable=True`; `deletable=False` → `not_deletable=True`). Old fields will be removed in a future version.

### DataSpec mutability flags

`not_editable=True` blocks both modifying existing rows and inserting new rows via `/storage/save` (both are write operations gated by `WRITE`; the storage enforcement treats them uniformly). `not_deletable=True` blocks deletion via `/storage/delete`.

| Scenario | `not_editable` | `not_deletable` |
|---|---|---|
| Full CRUD (default) | — | — |
| Edit-but-not-delete (retention) | — | `True` |
| Frozen content, deletable (purge-only, rare) | `True` | — |
| Fully frozen | `True` | `True` |

There is no schema-level expression for "append-only" (allow create but not edit) or "system-seeded singleton" (system creates, user edits, no creates by user) any more — both required separating creates from edits, which the merged two-flag model cannot do. Use handler-level enforcement or row-level permission policies for those shapes.

### Per-user overlay

`TypeResponse._apply_permission_flags` rewrites `not_editable` / `not_deletable` on the response based on the active `PermissionContext`:

- `effective_not_editable = bool(schema.not_editable) or not write_allowed`
- `effective_not_deletable = bool(schema.not_deletable) or not delete_allowed`

`write_allowed` / `delete_allowed` come from the permissions evaluator. When no `PermissionContext` is active or the type is in `PUBLIC_TYPES`, both are allowed. Admin-only types require `ADMIN` for both. Schema restrictions always win — the overlay never clears a restriction declared by the developer.

The cached `DataSpec` on each type holds the schema declaration only; the overlay clones the spec and rebuilds it. The cached instance is never mutated.

### Frontend Response Changes

The serialized `TypeSpec` carries:

- `NotEditable: bool | null` — `True` when the active user cannot edit (or insert via `/save`) rows of this type, whether by schema declaration or permission deficit.
- `NotDeletable: bool | null` — `True` when the active user cannot delete rows of this type.

Removed (no longer emitted): `NotCreatable`, `UserCanCreate`, `UserCanEdit`, `UserCanDelete`, `Editable`, `Deletable`, and `Readonly` (the DataSpec-level `Readonly`; `Readonly` on `FieldSpec` is unaffected and still emitted as a field-level UI hint).

### Server-side enforcement

The schema-level flags are enforced on the storage routes:

- `POST /storage/delete` returns **403** with detail `Type X is marked not_deletable; rows cannot be deleted.` when the target type's `DataSpec` declares `not_deletable=True`, regardless of the caller's `DELETE` permission.
- `POST /storage/save` returns **403** with detail `Type X is marked not_editable; rows cannot be saved.` when the target type's `DataSpec` declares `not_editable=True`, for both inserts and updates.

Enforcement reads the cached `DataSpec` (the developer's declaration), not the per-user overlay.

In-process write paths (handlers calling `DataSource.replace_one`, preload loaders, retention jobs) deliberately bypass this check; they are trusted to honor the schema contract on their own. The enforcement targets the public storage routes used by the UI and any external client.

### Migration Impact

- **Backend code declaring `DataSpec` flags:** Replace `readonly=True` / `editable=False` with `not_editable=True`, and `deletable=False` with `not_deletable=True`. Old fields continue to work via silent translation but should be migrated. There is no `not_creatable` — append-only and system-seeded scenarios that relied on it must move to handler-level checks.
- **Frontend code (BREAKING):** Stop reading `UserCanCreate` / `UserCanEdit` / `UserCanDelete`, `Editable` / `Deletable`, and `NotCreatable` from the type response — none are emitted any more. Use `NotEditable` and `NotDeletable` directly: they already reflect the active user's effective restrictions, no separate permissions request is required for CRUD-button decisions on the type listing. Stop reading `Readonly` from `TypeSpec` (DataSpec-level was removed); use `NotEditable` instead. Field-level `Readonly` on `FieldSpec` is unchanged.
- **External / non-UI clients:** Calls to `POST /storage/save` and `POST /storage/delete` reject mutations of types that declare schema-level restrictions — handle the new `403` responses.

---

## v2.0.3

### Summary

- **Added:** New `RecordUpdateEvent` on the `WS /events/` contract for server-side validation of a full `InteractiveMixin` candidate record without persisting it. Pairs with a new `InteractiveMixin.update_record(candidate)` hook.

### RecordUpdateEvent for Server-Side Validation

- **Added (`runtime/cl/runtime/ui/event/record_update_event.py`):** new `UiEvent` subclass `RecordUpdateEvent { Key, Record }`. The `Record` field carries the full serialized candidate record (PascalCase keys, `_t` discriminator).
- **Added (`runtime/cl/runtime/ui/event/record_update_event_handler.py`):** dispatches the event by deserializing the candidate (kept mutable so the hook can also normalize/derive fields) and forwarding it to `target.update_record(candidate)`. The hook returns the full response: on full success a single `RecordUpdateEvent` with the normalized candidate; on any failure one `UserErrorEvent` per failing field, optionally followed by a `RecordUpdateEvent` carrying the candidate as it stands (un-normalized for failed fields). The handler never writes to `DataSource`.
- **Added (`runtime/cl/runtime/records/interactive_mixin.py`):** new abstract hook `update_record(self, candidate: InteractiveMixin) -> list[UiEvent]`. Subclasses override to perform field-level checks and (optionally) normalize the candidate before serializing it back into the success event; implementations must NOT persist anything.
- **Changed (`runtime/cl/runtime/ui/event/event_manager.py`):** `SUPPORTED_EVENT_HANDLERS` now includes `RecordUpdateEvent → RecordUpdateEventHandler`.

### Affected Endpoints

| Route | Effect |
|-------|--------|
| `WS /events/` (`ui_events_router`) | Now accepts `{"_t": "RecordUpdateEvent", "Key": ..., "Record": {...}}` in addition to existing events. Server replies with: on full success a single `RecordUpdateEvent` with the normalized candidate; on any failure one `UserErrorEvent` per failing field, optionally followed by a `RecordUpdateEvent` with the un-normalized candidate. The DB is never modified by this event. |

### Client Migration

- No breaking change. Clients that don't send `RecordUpdateEvent` are unaffected.
- New clients can call this event for whole-record pre-save validation. Frontend `EventTypeEnum` (`ui-react/packages/common/src/types/eventType.ts`) now includes `RecordUpdate = 'RecordUpdateEvent'`.

---

## v2.0.2

### Summary

- **Added:** WebSocket connections now propagate the active dataset to the request context via a `dataset` URL query parameter. WebSocket sessions previously always defaulted to the root dataset.

### Dataset Propagation for WebSocket

Browsers cannot set custom request headers on the WebSocket upgrade, so WebSocket connections use a query string parameter instead of the HTTP `dataset` header.

- **Changed (`runtime/cl/runtime/routers/context_middleware.py`):**
  - For `scope["type"] == "http"`: still reads the `dataset` request header (unchanged).
  - For `scope["type"] == "websocket"`: now reads the `dataset` URL query parameter from `scope["query_string"]` (URL-decoded).
  - The `dataset` request header is no longer consulted for WebSocket scopes.
  - Other ASGI scope types (e.g. `lifespan`) are still ignored.
- **Changed (`runtime/cl/runtime/server/auth_dependency.py`):**
  - HTTP path keeps reading `request.headers.get("dataset")`.
  - WebSocket path now reads `websocket.query_params.get("dataset")` instead of `websocket.headers.get("dataset")`.

### Affected Endpoints

| Route | Effect |
|-------|--------|
| `WS /events/` (`ui_events_router`) | Control CRUD (`update_value`, `update_partial_value`, `replace_one`) and `InteractiveMixin` records now read/write in the dataset specified by the `dataset` query parameter on the WS URL. |

### Client Migration

- Frontend WebSocket clients must include the active dataset on the upgrade URL, URL-encoded, e.g.:
  - `wss://host/api/ui-events/events/?dataset=%5Cchild&key=...&type=...&viewer_name=...`
  - `\` must be encoded as `%5C` (`encodeURIComponent("\\child")` → `%5Cchild`).
- HTTP clients are unaffected — they continue to send the `dataset` request header.
- Connections established without the `dataset` parameter continue to default to the root dataset.

### Migration Impact

- Browser-based UIs that previously did not pass the dataset on WS will start writing controls/InteractiveMixin records into the root dataset by default. Update the WS client to append `?dataset=<encoded>` to the upgrade URL.
- Non-browser clients that previously sent a `dataset` header on the WS handshake must switch to the query-parameter form.

---

## v2.0.1

### Summary

- **Changed:** `GET /auth/me` `Scopes` field now returns group labels (human-readable names) instead of raw group IDs when available.

### MeResponse Scopes Changes

- **Changed:**
  - `Scopes` in `GET /auth/me` now resolves group IDs to their `Group.label` from the database.
  - If a `Group` record exists and has a label, the label is returned; otherwise the raw group ID is returned as before.
  - No change to the field name or type (`list[str]`).

### Migration Impact

- `Scopes` in `/auth/me` may now return different string values (labels vs IDs) — update any frontend logic that matches on exact scope strings.

---

## v2.0.0

### Summary

- **Breaking Change:** Schema system rewritten — all endpoints returning type schema now use `TypeSpec`-based classes instead of `TypeDecl`. Response structures, field names, and type representations are entirely different.
- **Breaking Change:** `GET /schema/type` response changed from flat `dict[str, dict]` keyed by `"module.TypeName"` to structured `TypeResponse` with `TypeSpec` + `Dependencies` keyed by `"TypeName"`.
- **Breaking Change:** `DataService.run_select_table`/`run_select_type` response changed — `schema_` (alias `Schema`) + `base_type` replaced by `type_spec` + `dependencies` + `query_schemas`.
- **Breaking Change:** `GET /auth/me` scopes now derived from `PermissionContext.groups` instead of hardcoded `["Read", "Write", "Execute", "Developer"]`.
- **Breaking Change:** All CRUD and task routes now enforce permissions via `PermissionEvaluator`. Unauthorized requests receive `403`.
- **Breaking Change:** Caching mechanism replaced — `cache_middleware.py` removed in favor of decorator-based `caching.py`.
- **Breaking Change:** `metrics_middleware.py` removed.
- **Added:** `DataService.run_load_record` — single-record load returning `LoadRecordResponse` with `record`, `type_spec`, `dependencies`.
- **Added:** `query_schemas` field in `SelectDataResponse` for query filter type schemas.
- **Changed:** `POST /storage/save` returns `400` when records missing `_t` field.
- **Changed:** `GET /storage/datasets` includes all intermediate levels, sorted by name.
- **Changed:** Auth cookies now include configurable `samesite` attribute.
- **Added:** OpenTelemetry trace context in request log scope.

### Schema System Migration (TypeDecl → TypeSpec)

All API endpoints returning type schema information now use the `TypeSpec` class hierarchy instead of `TypeDecl`. This affects `GET /schema/type`, `DataService.run_select_table`, `DataService.run_select_type`, and the new `DataService.run_load_record`.

#### Response dictionary keys

| Aspect | Old | New |
|--------|-----|-----|
| Key format | `"module.TypeName"` (e.g. `"cl.UiAppState"`) | `"TypeName"` (e.g. `"UiAppState"`) |
| Module prefix | Always present (`"cl."`) | Removed |

#### Type-level changes

| Old field | New equivalent | Notes |
|-----------|---------------|-------|
| `Module` | Removed | No module reference |
| `Name` | `TypeSpec.Type` | Moved inside TypeSpec |
| `Label` | `Label` | Same concept |
| `Comment` | Removed | |
| `TypeKind` | `TypeSpec.TypeKind` | Values changed (see below) |
| `DisplayKind` | Removed | Frontend must default to Basic |
| `Inherit` | Removed | No parent type reference |
| `Declare` | `Handlers` | Restructured |
| `Implement` | Removed | |
| `Elements` | `Fields` | Restructured (see below) |
| `Keys` | Removed | |
| `Abstract`, `Immutable`, `Permanent` | Removed | |

#### TypeKind values

| Old | New | Notes |
|-----|-----|-------|
| `Record` | `Record` | Unchanged |
| `Data` | `Data` | Unchanged |
| `Data` (for keys) | `Key` | Keys now correctly report as `Key` |
| `Enum` | `Enum` | Unchanged |
| — | `Primitive` | New |
| — | `Container` | New: list, dict, tuple |

#### Field representation (ElementDecl → FieldSpec + TypeHint chain)

Old system used mutually exclusive type slots (`Value`, `Enum`, `Key`, `Data`). New system uses a unified `TypeHint` chain via `FieldSpec.FieldTypeHint`.

| Old field | New equivalent | Notes |
|-----------|---------------|-------|
| `Name` (PascalCase) | `FieldSpec.FieldName` (snake_case) | Case changed |
| `Comment` | Removed | |
| `Value.Type` / `Enum` / `Key` / `Data` | `FieldTypeHint.SchemaType` + `TypeKind` | Unified |
| `Optional` | `FieldTypeHint.Optional` | Moved inside TypeHint |
| `Vector` | `TypeKind: Container` + `Remaining` chain | Replaced by nesting |
| `ReadOnly` | `Readonly` | Renamed (lowercase 'o') |
| `Format_` | Removed | |
| — | `Hidden`, `Empty`, `Label` | New fields, always present |

#### Primitive type names

| Old (`Value.Type`) | New (`SchemaType`) |
|--------------------|--------------------|
| `String` | `str` |
| `Double` | `float` |
| `Bool` | `bool` |
| `Int` | `int` |
| `Long` | `int` (with subtype) |
| `Date` | `date` |
| `Time` | `time` |
| `DateTime` | `datetime` |
| `UUID` | `UUID` |
| `Binary` | `bytes` |

#### Handler representation

| Old | New | Notes |
|-----|-----|-------|
| `Declare.Handlers[].Name` | `Handlers[].HandlerSpec.Name` | Moved inside spec |
| `Declare.Handlers[].Label` | `Handlers[].Label` | At props level |
| `Declare.Handlers[].Type_` | `HandlerSpec.Type_` | Values: `job`, `viewer`, `process`, `content` |
| `Declare.Handlers[].Params` | `HandlerSpec.Params` (spec) + `Params` (with labels) | Dual representation |
| `Declare.Handlers[].Return` | Removed | |
| `Implement` block | Removed | |
| Synthetic `"{Type}{Handler}Args"` entries | Removed | |
| — | `Hidden` on handler | New |
| — | `Label` on handler params | New |

### Route-by-Route Changes

#### `GET /schema/type`

- **Old:** Returns `dict[str, dict]` — flat dict of TypeDecl entries keyed by `"module.TypeName"`, including synthetic table items and handler args schemas.
- **New:** Returns `TypeResponse` with `TypeSpec` (serialized type spec) and `Dependencies` (dict keyed by `"TypeName"`), built via BFS of fields and handler parameters.
- Returns `403` when user lacks permission (`PermissionEvaluator.can_see_type`).

#### `DataService.run_select_table` / `run_select_type`

- **Old `SelectDataResponse`:** `schema_` (alias `Schema`, full TypeDecl dependency dict) + `base_type` (common base type name) + `data`.
- **New `SelectDataResponse`:** `type_spec` (single serialized TypeSpec for common base type) + `dependencies` (dict of TypeSpec dependencies) + `query_schemas` (query filter schemas, nullable) + `data`.
- Now accepts optional `query_dict` parameter for query-based filtering.
- Data serialized with `FOR_UI_NO_NULLS` (omits null fields).
- Row-level permission filtering applied after serialization.

#### `DataService.run_load_record` (new)

Single-record load replacing bulk `POST /storage/load` for UI use cases.

- **Parameters:** `type_name: str`, `key: str` (serialized key string).
- **Returns `LoadRecordResponse`:** `record` (single serialized dict, FOR_UI with nulls) + `type_spec` + `dependencies`.
- Returns empty `LoadRecordResponse` (all fields `None`) if record not found.

#### `DataService.run_screens`

- Now filters tables and types by `PermissionEvaluator.can_see_type`. Types the user cannot access are excluded from the screen list.

### Auth Changes

- **`GET /auth/me` — `scopes`:** Previously hardcoded `["Read", "Write", "Execute", "Developer"]`. Now derived from `PermissionContext.groups`. Returns `[]` when no permission context is active.
- **Cookie `samesite`:** Auth cookies and `frontend_referer` cookie now include `samesite` attribute configured via `AuthSettings.auth_cookie_same_site`. Login callback uses centralized `set_auth_cookies()`.

### Permission Enforcement

All storage and task routes now check permissions. Clients may receive `403` responses.

| Route | Permission Check |
|-------|-----------------|
| `POST /storage/load` | Type-level `READ` + row-level filtering |
| `POST /storage/select` | Type-level `READ` + row-level filtering |
| `POST /storage/save` | Type-level `WRITE` per `_t` + row-level check |
| `POST /storage/delete` | Type-level `DELETE` + row-level check before deletion |
| `POST /task/run` | `EXECUTE` on type and handler |
| `POST /task/submit` | `EXECUTE` on type and handler |
| `GET /schema/type` | `can_see_type` check |

### Other Changes

- **`POST /storage/save`:** Validates `_t` field presence. Returns `400` with indices of records missing `_t`.
- **`GET /storage/datasets`:** Expands all intermediate dataset levels. Sorted by name.
- **Caching:** `cache_middleware.py` (HTTP-level) replaced by `caching.py` (decorator `@cacheable(ttl=N)`, auth-aware cache keys, graceful Redis failure handling).
- **Middleware:** `metrics_middleware.py` removed. `log_middleware.py` now injects OpenTelemetry `trace_id`/`span_id` when telemetry enabled.

### Migration Impact

- **Schema parsing completely changed.** Response is no longer a flat dict — it has `TypeSpec` + `Dependencies` top-level keys. Dictionary keys drop the module prefix. Field names in schema are snake_case (was PascalCase). Primitive type names use Python names (was schema-specific). See tables above for full mapping.
- **`DisplayKind` removed.** Frontend should default to `Basic` display mode.
- **Select responses restructured.** `schema_` (alias `Schema`) + `base_type` replaced by `type_spec` + `dependencies` + `query_schemas`.
- **New `run_load_record` handler** replaces bulk load for single-record UI scenarios.
- **Dynamic scopes.** `scopes` in `/auth/me` depends on user's permission groups.
- **Handle `403` responses** on all storage and task routes.
- **`POST /storage/save`** requires `_t` in every record (now returns `400` if missing).
- **`metrics_middleware.py` removed.** Replace with OpenTelemetry metrics if needed.

---

## v1.10.4

### Summary

- **Changed:** `GET /storage/datasets` response now includes declared datasets (from `DatasetKey` records) merged with actual datasets found in the database.
- **Changed:** `DatasetKey.dataset_id` now requires a leading separator (`\`), e.g. `\` for root or `\abc` for a child dataset.

### Datasets Response Changes

- **Behavior change:**
  - `DatasetsResponseItem.get_datasets()` now loads all `DatasetKey` records from the database and merges their `dataset_id` values with the datasets discovered via `Db.get_datasets()`.
  - The merged set is deduplicated, so datasets that exist both as stored records and as `DatasetKey` declarations appear only once.
  - This allows the UI to display datasets that have been declared but do not yet contain any records.

### DatasetKey Validation

- **Changed:**
  - `DatasetKey` now validates in its `__init` hook that `dataset_id` starts with the dataset separator character (`\`).
  - Invalid identifiers raise a `RuntimeError` with a descriptive message.
  - Examples of valid identifiers: `\` (root), `\abc` (child dataset).

### Migration Impact

- No breaking changes to the API contract. The `/storage/datasets` response shape is unchanged; it may now return additional dataset entries that were previously omitted.
- Code that constructs `DatasetKey` without a leading `\` in `dataset_id` will now raise a `RuntimeError` at build time.

---

## v1.10.3

### Summary

- **Added:** Optional `type_name` and `method` query params on `POST /task/run`, `POST /task/submit`, and `type_name` on `POST /storage/select`.
- **Changed:** `BaseRunRequestBody.type` and `BaseRunRequestBody.method` are now optional (nullable) to support query-param-only requests.
- **Changed:** `SelectRequestBody.type` is now optional (nullable) to support query-param-only requests.

### Route Parameter Changes

The following routes now accept scalar identifiers as query parameters for easier debugging in the browser Network tab. When provided, query params take priority over the corresponding body fields. Body-only requests remain fully supported (backward compatible).

| Route | New Query Params | Body Fields Affected |
|-------|-----------------|---------------------|
| `POST /task/run` | `type_name`, `method` | `type` and `method` now optional |
| `POST /task/submit` | `type_name`, `method` | `type` and `method` now optional |
| `POST /storage/select` | `type_name` | `type` now optional |

**Not changed:** `key` (can contain arbitrary characters), `task_run_ids` (variable-length lists), and `arguments` (complex dicts) remain body-only.

### New Utility

- `RouteUtil.resolve()` in `cl/runtime/routers/route_util.py` — shared helper for resolving query-or-body parameters with 422 error on missing required fields.

### Migration Impact

- No breaking changes. All existing body-only requests continue to work unchanged.
- New query params are optional — clients can adopt them incrementally.

---

## v1.10.2

### Summary

- **Added:** Optional nested `features` field (`AppFeatures`) to `SettingsResponse` for grouping UI feature flags.
- **Removed:** Deprecated `sources` field from `SettingsResponse`.

### SettingsResponse Changes

- **Added:**
  - `features: AppFeatures | None` — optional nested object containing application feature flags. Defaults to `None`.

- **Removed:**
  - `sources: list[EnvInfo] | None` — previously deprecated field listing data sources. Use `EnvService` instead.

### AppFeatures Model

New nested Pydantic model returned inside `SettingsResponse.features`:

- `envs_support: bool | None` — when `True`, enables environment management features in the UI; when `False` or `None`, environment features are hidden.
- `db_tools: bool | None` — when `True`, enables database tools in the UI; when `False` or `None`, database tools are hidden.
- `ai_chat: bool | None` — enables or disables the AI Chat feature.
- `dataset_support: bool | None` — enables dataset integration and manipulation features.
- `demo_mode: bool | None` — activates demo mode for presentations or testing.

### Deprecated Fields in SettingsResponse

The following top-level fields are now deprecated in favor of their counterparts inside `features`:

- `chat_about_on` — use `features.ai_chat` instead.
- `dataset_support` — use `features.dataset_support` instead.
- `demo_mode` — use `features.demo_mode` instead.

These fields remain for backward compatibility but will be removed in a future version.

### Migration Impact

- **Breaking:** The `sources` field has been removed from `SettingsResponse`. Frontend code that relied on this field should use `EnvService` instead.
- The new `features` field is optional and defaults to `None`.
- When present, the JSON payload includes a nested `Features` object with PascalCase keys (`EnvsSupport`, `DbTools`, `AiChat`, `DatasetSupport`, `DemoMode`).
- Frontend should migrate from top-level `chat_about_on`, `dataset_support`, `demo_mode` to the nested `features` equivalents.

---

## v1.10.1

### Summary

- **Added:** Optional `handlers_pinned_by_default` boolean field to `UiAppState` to pin handlers to the toolbar by default.

### UiAppState Changes

- **Added:**
  - `handlers_pinned_by_default: bool | None` — when `True`, handlers are pinned to the toolbar by default; when `False` or `None`, the existing behavior is preserved.

### Migration Impact

- No breaking changes. The new field is optional and defaults to `None`.

---

## v1.10.0

### Summary

- **Breaking Change:** WebSocket route renamed from `/control_events/` to `/events/` — now a universal gateway for both Controls and InteractiveMixin records.
- **Breaking Change:** Event base class renamed from `ControlEvent` to `UiEvent`; field `control_path` renamed to `key`.
- **Breaking Change:** `ValueUpdateEvent` and `PartialValueUpdateEvent` field `key` renamed to `field`.
- **Added:** `InteractiveMixin` — a new mixin enabling any Record to send/receive WebSocket events without being a Control.
- **Added:** `TargetResolver` abstraction with `ControlTargetResolver` and `RecordTargetResolver` implementations.
- **Changed:** `EventManager` now accepts a `TargetResolver` instead of a root `Control` node.

### WebSocket Route Changes

- **Renamed:** `/control_events/` → `/events/`
  - When `viewer_name` is provided, the endpoint resolves a `Control` via `ControlTargetResolver` (existing behavior).
  - When `viewer_name` is empty, the endpoint resolves an `InteractiveMixin` record via `RecordTargetResolver`.

### Event Model Changes

- **Renamed classes:**
  - `ControlEvent` → `UiEvent` (base class for all WebSocket events)
  - `ControlEventHandler` → `UiEventHandler` (base class for event handlers)

- **Renamed fields in `UiEvent` (formerly `ControlEvent`):**
  - `control_path` → `key` — now represents either a control path or a record key in the database.

- **Renamed fields in `ValueUpdateEvent`:**
  - `key` → `field` — name of the record field that changed.

- **Renamed fields in `PartialValueUpdateEvent`:**
  - `key` → `field` — name of the record field whose part changed.

- **Renamed fields in `ControlUpdateEvent`:**
  - `control_path` (inherited) → `key` (inherited from `UiEvent`).

- **Renamed fields in `LayoutUpdateEvent`:**
  - `control_path` (inherited) → `key` (inherited from `UiEvent`).

### InteractiveMixin

New mixin class (`cl.runtime.records.interactive_mixin.InteractiveMixin`) enabling any Record to participate in WebSocket event handling:

- `update_value(field, value) -> list[UiEvent]` — update one field, persist to DB, return events.
- `update_partial_value(field, value, index) -> list[UiEvent]` — update part of a field, persist to DB, return events.
- `get_partial_value_type_hint(field_type_hint, index) -> TypeHint` — resolve type hint for indexed field parts.

### Target Resolver Pattern

New resolver abstraction replaces direct `Control` loading in `EventManager`:

- `TargetResolver` (abstract base) — `resolve(target_id) -> T`
- `ControlTargetResolver` — resolves Controls by control path via `ControlLoader` (replaces the former `EventManager._load_control` method).
- `RecordTargetResolver` — resolves `InteractiveMixin` records by deserializing a semicolon-delimited key string and loading from `DataSource`.

### Control Method Signature Changes

- `update_value(key, value)` → `update_value(field, value)`
- `update_partial_value(key, value, index)` → `update_partial_value(field, value, index)`
- `on_change(control_path, key, value)` → `on_change(key, field, value)`
- `update_control(**kwargs)` return type changed from `list[ControlEvent]` to `list[UiEvent]`
- `update_layout()` return type changed from `list[ControlEvent]` to `list[UiEvent]`

### Migration Impact

- **WebSocket URL:** Frontend must connect to `/events/` instead of `/control_events/`.
- **Event field names:** All event JSON payloads must use `Key` (formerly `ControlPath`) and `Field` (formerly `Key` in value update events).
- **Event type names:** Replace references to `ControlEvent` with `UiEvent` and `ControlEventHandler` with `UiEventHandler`.
- **InteractiveMixin support:** The WebSocket endpoint now supports direct record interaction when `viewer_name` is omitted from the connection query parameters.

---

## v1.9.4

### Summary

- **Changed:** `DataService.select_table` and `DataService.select_type` now omit fields with `None` values from serialized record data.
- **Changed:** `UiRecordUtil.ExportRecords` now accepts an `export_format` parameter (`SaveFormat` enum: `JSON`, `YAML`, `CSV`) and returns a `FileData` ZIP archive instead of saving to disk.
- **Added:** `UiRecordUtil.SavePermanentlyRecords` handler to save records to the preloads directory for permanent storage.
- **Added:** `SaveFormat` enum (`JSON`, `YAML`, `CSV`) replacing the former `ExportRecordsFormat`.

### DataService Changes

- **Behavior change:**
  - `select_table` and `select_type` responses no longer include keys where the value is `None`. Previously all fields were included with explicit `null` values.
  - The `base_type` field in the response is unaffected and still includes all fields.

### UiRecordUtil Changes

- **Changed:**
  - `ExportRecords(type_to_export, keys, with_dependencies, export_format)`:
    - Added `export_format: SaveFormat = SaveFormat.JSON` parameter to specify the serialization format.
    - Now returns a `FileData` object containing a ZIP archive with the serialized records, instead of saving directly to the preloads directory.
    - Supports `JSON`, `YAML`, and `CSV` formats.

- **Added:**
  - `SavePermanentlyRecords(type_to_save, keys, with_dependencies, save_format)`:
    - Saves records to the first configured preloads directory for permanent storage.
    - `type_to_save: str` — Type name of the records to save.
    - `keys: list[str]` — List of serialized keys identifying records to save.
    - `with_dependencies: bool = False` — If `True`, include all dependent records.
    - `save_format: SaveFormat = SaveFormat.JSON` — Format for serialization (default `JSON`).

### SaveFormat Enum

Replaces the former `ExportRecordsFormat`. Defined in `cl.runtime.records.save_format`.

- `JSON` — JSON format.
- `YAML` — YAML format.
- `CSV` — CSV format.

### Migration Impact

- Frontend table and type views should no longer expect `null` values for empty fields in record data — absent keys indicate `None`.
- Frontend code calling `ExportRecords` should handle the returned `FileData` ZIP archive instead of expecting server-side file persistence.
- Use the new `SavePermanentlyRecords` handler to persist records to the preloads directory.
- Replace any references to `ExportRecordsFormat` with `SaveFormat`.

---

## v1.9.3

### Summary

- **Changed:** The `/settings` route (`SettingsResponse`) now returns the **`cl.runtime.routers`** module version for `contract_version` and `schema_version`, instead of the global runtime package version. This aligns the API contract version with the version of the routes/API layer that defines the backend-frontend contract.

### Settings Response Changes

- **Behavior change:**
  - `contract_version` and `schema_version` are now sourced from `cl.runtime.routers.__version__` (via `VersionUtil.get_module_version(module="cl.runtime.routers")`) rather than the global `cl.runtime` (or `_version.py`) version.
  - Frontend and clients can rely on this value to reflect the API/routes contract version for compatibility checks.

### Migration Impact

- No breaking change: the field names and semantics are unchanged; only the source of the version string has changed.
- If you were comparing against a global runtime version, update your checks to expect the `cl.runtime.routers` version (e.g. `1.9.3`) instead.

---

## v1.9.2

### Summary

- **Added:** Introduced `EnvService` to handle environment-related operations and provide structured environment management.
- **Added:** Introduced `Environments` record to manage environment configuration with active environment tracking.
- **Deprecated:** The `/storage/envs` route and `EnvResponseItem` model are now deprecated in favor of `EnvService`.

### EnvService description

- **Capabilities:**
  - Environment Management: Provides information about available environments stored in the database.
  - Active Environment Control: Allows setting the active environment by name with validation.

- **Handlers:**
  - `run_envs()`: Returns `Environments` record containing the active environment name and list of available environments as `EnvDescriptor` objects. Creates default configuration if none exists.
  - `run_set_active_env(env_name)`: Sets the specified environment as active by updating the `active_env_name` field in the `Environments` record. Validates that the environment exists before setting.

### Environments Model

The `Environments` is a Pydantic-based record that manages environment configuration:

- **Key:** `EnvironmentsKey` (singleton key with `id="default"`)
- **Fields:**
  - `active_env_name: str | None` - Name of the currently active environment.
  - `envs: list[EnvDescriptor] | None` - List of available environment descriptors.
- **Validation:** The `__init` method validates that all environment names in the `envs` list are unique, raising a `RuntimeError` if duplicates are found.

### EnvDescriptor Model

The `EnvDescriptor` is a Pydantic-based data class that represents environment metadata:

- **Fields:**
  - `env_name: str` - Name of the environment.
  - `parent: str | None` - Name of the parent environment.
  - `url: str | None` - URL of the environment backend API. None if matches current backend URL.
  - `description: str | None` - Description of the environment backend API.

### Deprecated Routes and Models

- **Deprecated:**
  - `/storage/envs` route is now deprecated. Use `EnvService.run_envs()` handler instead.
  - `EnvResponseItem` Pydantic model is now deprecated. Please use  `EnvService` directly.

### Migration Impact

- Frontend code that uses the `/storage/envs` route should migrate to use the `EnvService.run_envs()` handler.
- The handler returns an `Environments` object containing both the active environment name and the list of available environments.
- Active environment tracking is now managed through the `Environments.active_env_name` field via EnvService.
- The route continues to work for backward compatibility but will show deprecation warnings.

---

## v1.9.1

### Summary

- **Added:** Introduced `contract_version` field to the `/settings` route (`SettingsResponse`) to explicitly track the backend-frontend API contract version.
- **Deprecated:** `schema_version` field in `SettingsResponse` is now deprecated in favor of `contract_version`. It will be removed in a future version.

### Settings Response Changes

- **Added:**
  - `contract_version: str` - Version of the backend-frontend API contract. Used to ensure compatibility between backend and frontend. This field replaces `schema_version` with a clearer, more descriptive name.

- **Deprecated:**
  - `schema_version: str` - Marked as deprecated. Use `contract_version` instead. This field will be removed in a future version.

### Migration Impact

- Frontend code should migrate from using `schema_version` to `contract_version` for API contract version checks.
- Both fields currently return the same value for backward compatibility.
- The deprecation warning will be raised when accessing `schema_version`.

---

## v1.9.0

### Summary

- **Breaking Change:** Added `user_secrets_public_key` to the `/auth` route to support user-specific secrets management.
- **Added:** Added `session_id` to the `/settings` route.

## v1.8.0

### Summary

- **Added:** Introduced `DataService` to handle data-related operations and provide structured data access from the UI.
- **Changed:** Updated `UiAppState.opened_tabs` to integrate with `DataService`.

### DataService description

- **Capabilities:**
  - Screen Management: Provides information about available screens, including tables, types, and filters, that can be displayed based on database records.
  - Data Retrieval: Facilitates the retrieval of records from the database by table, type, or filter.

- **Handlers:**
  - `screens()`: Returns data about screens (tables, types, filters).
  - `select_table(table_name, skip, limit)`: Retrieves records from the database by table name with optional pagination.
  - `select_type(type_name, skip, limit)`: Retrieves records from the database by type name with optional pagination.
  - `select_filter(table_name, filter_name)`: Retrieves records from the database by filter (not implemented).

### Opened Tabs Changes

`TabInfo` fields were simplified and flattened to better reflect the context of opened tabs in the UI.

- **Removed:**
  - `type` and `key` fields were removed.

- **Added:**
  - `table_name: str | None` - Name of an opened table.
  - `type_name: str | None` - Name of an opened record type.
  - `filter_name: str | None` - Name of an opened filter.

---

## v1.7.0

### Summary

- **Changed:** `layout` and `maximized_tab_id` fields were marked obsolete in `UiTypeState`. `UiTypeLayout` model was introduced to manage type layout.

#### UiTypeLayout definition:

  - Key fields:
  - `type_`: TypeDeclKey
  - `user`: UserKey | null

  - Basic fields:
  - `layout`: list of LayoutElementBase | null
  - `maximized_tab_id`: string | null

---


## v1.6.2

### Summary

- **Changed:** Authorization JWT tokens has been moved from response `payload` to `cookies` as `"access_token"` and `"refresh_token"`

---

## v1.6.1

### Summary

- **New Feature:** Added `user_secrets_public_key` to the `/auth` route to support user-specific secrets management.
- **Non-breaking Change:** Added default value for `email_from` setting in support configuration.
- **Removed:** `event_transport` field from Settings response as it's no longer needed. ApiSettings.server_event_transport removed as well.

### Support Settings Changes

- **Changed:**
  - `email_from` field in `SupportSettings` now has a default value of `"ui.feedback@compatibl.com"`
  - This field is no longer required in configuration files, making setup easier

### Settings Response Changes

- **Removed:**
  - `event_transport` field has been removed from the Settings response. This field is no longer needed as SSE (Server-Sent Events) is now the default and only event transport mechanism

### Authentication & User Secrets

- **Added:**
  - `user_secrets_public_key` field to the `/auth` route for user-specific secrets management

#### User Secrets Encryption Flow

Users can now manage their own encrypted secrets. The frontend uses the `/auth` route to obtain the `user_secrets_public_key` for encrypting and storing user-level secret keys (such as OPENAI API keys) in browser. These encrypted secrets are then passed to backend tasks via additional HTTP headers.

**Frontend Process:**

1. Retrieve `user_secrets_public_key` from `/auth` endpoint
2. Encrypt sensitive user secrets (API keys, etc.) using the public key
3. Store encrypted secrets in browser for persistence
4. Pass encrypted secrets to backend tasks via headers: `cl-user-key-{key-name}`

**Backend Integration:**

- Tasks can now receive user-specific encrypted secrets through standardized header naming
- Header format: `cl-user-key-{key-name}` (e.g., `cl-user-key-openai-api-key`)
- Enables secure, user-specific configuration for external service integrations

### Migration Impact

- **No breaking changes:** Existing configurations will continue to work as before
- **Optional configuration:** The `email_from` setting can now be omitted from configuration files
- **Backward compatibility:** Explicitly setting `email_from` will override the default value

---


## v1.6.0

### Summary

- **Breaking Changes:** Renamed fields in SSE events for better clarity and consistency.
- **Deprecated:** `event_transport` setting is deprecated and will be removed in the next version. SSE will be used by default.

### SSE Events Field Renames

The following field names have been changed in SSE events for improved clarity:

#### Event Base Class
- **Changed:** `event_type` → `event_kind` in `cl/runtime/events/event.py`

#### Log Events
- **Changed:** `record_type` → `record_type_name` in `cl/runtime/events/log_event.py`
- **Changed:** `record_type` → `record_type_name` in `cl/runtime/log/log_message.py`

### Settings Changes

- **Deprecated:** `event_transport` setting is deprecated and will be removed in the next version.
- **Default Behavior:** SSE (Server-Sent Events) will be used by default for all event communication.

### Migration Impact

- Frontend code that references the renamed fields must be updated:
  - Update `event_type` references to `event_kind`
  - Update `record_type` references to `record_type_name`
- The `event_transport` setting can be removed from configuration files as it will no longer be used.

---

## v1.5.1

### Summary

- Added new optional fields to Control: `label`, `enabled`, and `collapsible` for enhanced UI customization.
- Changed default event transport from "NO_SSE" to "SSE" in settings.

### Control Enhancements

- **Added:**
  - `label: str | None = control_field(default=None)` - The control label displayed in the UI when specified.
  - `enabled: bool | None = control_field(default=True)` - Controls whether the control should be enabled or disabled.
  - `collapsible: bool | None = control_field(default=None)` - Indicates whether the control can be collapsed in the UI to reduce its size on the panel. If enabled, a collapse/expand icon will be displayed.

### Settings Changes

- **Changed:**
  - Default `event_transport` setting changed from "NO_SSE" to "SSE".

---

## v1.5.0

### Summary

- Handler declarations returned to frontend now do not contain handler prefixes.
- Added `ContentUtil` class for managing records as contents.
- Added `UiRecordUtil.run_load_record_content` handler for record as content retrieval.

### Ui*Util Handler Naming Changes

This is a **breaking change** affecting all Ui*Util handler method names. Previously, the frontend used PascalCase method names with "Run" prefix. Now handler names are returned without the "Run" prefix.

#### Affected Ui*Util Classes and Their Handlers:

**UiSupportUtil:**
- `SaveFrontendError` (previously `RunSaveFrontendError`)
- `GetFeedbackFormDetails` (previously `RunGetFeedbackFormDetails`)
- `SendFeedback` (previously `RunSendFeedback`)
- `DownloadLogs` (previously `RunDownloadLogs`)

**UiRecordUtil:**
- `GetRecordPanels` (previously `RunGetRecordPanels`)
- `LoadRecordPanel` (previously `RunLoadRecordPanel`)
- `ExportRecords` (previously `RunExportRecords`)
- `SavePermanently` (previously `RunSavePermanently`)
- `LoadRecordContent` (previously `RunLoadRecordContent`)

**UiLogUtil:**
- `GetErrorLogs` (previously `RunGetErrorLogs`)
- `GetFlatLogs` (previously `RunGetFlatLogs`)
- `GetLogsByTask` (previously `RunGetLogsByTask`)

#### Migration Impact:
- Frontend code that references handler methods by name must be updated to use the new naming convention.
- The change affects all handler method calls to Ui*Util classes.
- This is a breaking change that requires frontend updates.

## v1.4.0

### Summary

- Merge `auth/{provider_id}/refresh-token` and `auth/{provider_id}/refresh-token-redirect`  to `auth/{provider_id}/refresh`
- Rename `auth/{provider_id}/login-redirect` to `auth/{provider_id}/callback`
- Rename `auth/{provider_id}/logout-redirect` to `auth/{provider_id}/logout`
- Rename `auth/m2m/api-key"` to `auth/m2m/token`

## v1.3.0

### Summary

- Added `UiLogUtil.run_get_error_logs` utility for retrieving recent error logs.
- Added `readable_time` field to `LogEvent` for human-readable UTC timestamps in log events.
- Log event serialization now outputs JSON strings for SSE protocol compliance.

### SSE (Server-Sent Events)

- **Event Serialization**: SSE events are now serialized as JSON strings in the `data` field, ensuring compliance with the SSE protocol and improving frontend compatibility.
- **LogEvent**: Added `readable_time` (string, UTC) to provide a human-readable timestamp for each log event.

### Utils

- **UiLogUtil**: Added `run_get_error_logs()` method to retrieve the last 1000 error log messages, sorted by timestamp (descending). This enables efficient error log history retrieval for UI and monitoring purposes.

### Sample Events

#### LogEvent

```
{
  "event_type": "LOG",
  "timestamp": "2025-06-30T16:18:57.123Z",
  "readable_time": "2025-06-30 16:18:57 UTC",
  "level": "Info",
  "message": "Handler started successfully.",
  "record_type": "Task",
  "handler_name": "run_with_error",
  "record_key": "abc123",
  "task_run_id": "run-001"
}
```

#### Error Event

```
{
  "event_type": "ERROR",
  "timestamp": "2025-06-30T16:19:00.456Z"
}
```

#### Output from `UiLogUtil.run_get_error_logs`

```
[
  {
    "event_type": "LOG",
    "timestamp": "2025-06-30T16:19:00.456Z",
    "readable_time": "2025-06-30 16:19:00 UTC",
    "level": "Error",
    "message": "Error in handler.",
    "record_type": "Task",
    "handler_name": "run_with_error",
    "record_key": "abc123",
    "task_run_id": "run-001"
  },
  // ... more error log messages ...
]
```

---

## v1.2.5

### Summary

- Added the `email_to` parameter to the `send_feedback` handler in `UiSupportUtil`.
- Now, feedback emails can be sent to a custom list of recipients, not just the default from settings.
- If `email_to` is not provided, the handler falls back to the default recipients from settings.

## v1.2.4

### Summary

- Added the `provider_id` query parameter to the `GET /auth/{provider_id}/login-redirect` endpoint.
- The login redirect callback now includes both `one_time_token` and `provider_id` as query parameters.
- This change improves support for multiple authentication providers and allows the frontend to distinguish the provider in the callback.
- Rename `auth/{provider_id}/renew` to `auth/{provider_id}/refresh-token`
- Rename `auth/{provider_id}/renew-redirect` to `auth/{provider_id}/refresh-token-redirect`

## v1.2.3

### Summary

- Added new SSE routes: `/sse/events` (event stream) and `/sse/log_history` (log history).
- Described new SSE event types: PING, LOG, ERROR, WARNING, TASK_STARTED, TASK_FINISHED.
- Added handler identification fields to TaskStartedEvent and TaskFinishedEvent: `record_type`, `record_key` (null if the handler is static), `handler_name`.
- Added `status` field to TaskFinishedEvent (`Completed` or `Failed`).
- Added utilities for retrieving log history in two ways: flat list (`RunGetFlatLogs`) and grouped by task_run_id (`RunGetLogsByTask`).
- UI should support an interactive log panel in two modes: flat list and by tasks.

### SSE API

- **GET /sse/events** — returns an endless stream of events (EventSourceResponse).
- **GET /sse/log_history** — returns a list of LogMessage objects (last 1000 records, ordered by descending timestamp; temporary until queries are supported).

#### Event types in /sse/events:
- `PING` — ping event every 15 seconds
- `LOG` — event with a log message
- `ERROR` — error event
- `WARNING` — warning event
- `TASK_STARTED` — task started event (contains `run_id`, `record_type`, `record_key`, `handler_name`)
- `TASK_FINISHED` — task finished event (contains `run_id`, `record_type`, `record_key`, `handler_name`, `status`)
- `NO_ACTIVE_TASKS` — event that there are no active tasks

#### Event definitions:

- **Base Event (SseEvent):**
  - `event_type`: string (one of: ERROR, WARNING, PING, LOG, TASK_STARTED, TASK_FINISHED, NO_ACTIVE_TASKS)
  - `timestamp`: string (ISO8601, UTC)

- **LogEvent:**
  - Inherits from SseEvent
  - `level`: string (Debug, Info, Warning, Error, Critical)
  - `message`: string
  - `record_type`: string | null
  - `handler_name`: string | null
  - `record_key`: string | null
  - `task_run_id`: string | null

- **TaskEvent:**
  - Inherits from SseEvent
  - `task_run_id`: string
  - `record_type`: string
  - `handler_name`: string
  - `record_key`: string | null

- **TaskFinishedEvent:**
  - Inherits from TaskEvent
  - `status`: string (Completed, Failed, etc.)

- **PING, ERROR, WARNING:**
  - Use the base SseEvent structure. Additional fields may be present depending on implementation, but typically only `event_type` and `timestamp` are required.

#### Changes in events:
- `TaskStartedEvent` and `TaskFinishedEvent` now include: `record_type`, `record_key` (null if static), `handler_name`.
- `TaskFinishedEvent` now includes `status` (`Completed` if no errors, `Failed` if there are errors).
- `ErrorEvent` and `WarningEvent` remain unchanged.

#### Log utilities:
- All logs in a single list: `/handler/run`, `Type: UiLogUtil`, `Method: RunGetFlatLogs`
- Logs by tasks: `/handler/run`, `Type: UiLogUtil`, `Method: RunGetLogsByTask`

#### UI recommendations:
- For real-time updates, listen to LogEvent in the Event Stream.
- For history, use the appropriate handler.

---

# API Changes

This document is a cumulative changelog for all API versions.

---

## v1.2.2

### Summary

- Extended `UiTypeState` with optional `page_index` and `page_size` properties.
- Updated the `CardControl` data model.

### UiTypeState

- **Added:**
  - Optional `page_index` property.
  - Optional `page_size` property.

### CardControl

- **Changed:**
  - Data model updated (see model documentation for details).

---

## v1.2.0 → v1.2.1

### Summary

- All fields except for `schema_version` in `SettingsResponse` are now optional.
- The `sources` field is now marked as **DEPRECATED** and will be removed in a future version. The frontend should use `/storage/envs` instead.

### SettingsResponse

- **Changed:**
  - `schema_version`: Now explicitly set to `"1.2.1"`.
  - All fields except `schema_version` are now optional.

- **Deprecated:**
  - `sources`: Marked as **DEPRECATED** and will be removed in a future version.

---

## v1.1 → v1.2.0

### Summary

- Application metadata such as name, version information, and session ID should now be accessed via the `/settings` endpoint and the `SettingsResponse` model.
- The `UiAppState` model should only be used for user specific UI state and not for application metadata.
- Extended settings with required flags to control UI.

### UiAppState

- **Removed fields:**
  - `backend_version`: Removed from `UiAppState`.

- **Deprecated fields:**
  - `application_name`: Deprecated in `UiAppState`, now provided by `SettingsResponse`.
  - `versions`: Deprecated in `UiAppState`, now provided by `SettingsResponse`.

  These fields remain in `UiAppState` for backward compatibility but should not be used in new code.

### API Routes

- **/settings (SettingsResponse). Added fields:**
  - `application_name`: Application name.
  - `versions`: Dictionary of component/package names and their versions.
  - `environment`: Active application environment (e.g., 'dev', 'staging', 'prod').
  - `event_transport`: Server event transport mechanism used for frontend-backend event communication.
  - `sources`: List of data sources configured for the application.
  - `chat_about_on`: Enables or disables the 'Chat About' feature.
  - `demo_mode`: Activates demo mode for presentations or testing.
  - `dataset_support`: Enables dataset integration and manipulation features.
  - `refresh_on_all_handlers`: Automatically refreshes the main data grid after any successful handler execution.
  - `grid_max_lines`: Maximum number of visible lines per cell in the main grid.
  - `hide_empty_columns`: Automatically hides columns in the grid that have no data across all rows.
  - `hide_handlers_in_full_screen_mode`: Controls whether handler controls are hidden in full-screen mode.

---

## v1.0 → v1.1

### Summary

- The `/settings` route and `SettingsResponse` model centralize application and environment metadata.
- The `/storage/envs`, `/support/save_frontend_error`, `/support/send_feedback`, `/panel`, `/entity/panels`, and `/export` routes are deprecated in favor of new handler-based utility classes.
- Migrate integrations to use the new utilities and `/settings` endpoint for future compatibility.

### API Routes

- **Added:**
  - Introduced the `/settings` route with the `SettingsResponse` model for unified application and environment metadata.

- **Deprecated / Obsoleted:**
  - The `/storage/envs` route is now **deprecated**. Use `/settings` for environment and source information.
  - The following routes are now **deprecated** and will be replaced by handler-based utilities:
    - `/support/save_frontend_error`
    - `/support/send_feedback`
    - `/panel`
    - `/entity/panels`
    - `/export`

### Utility Classes

- **Added:**
  - Introduced `UiSupportUtil`, `UiRecordUtil` classes.
    - These provide handler-based replacements for the deprecated `/support`, `/panel`, and `/export` routes.

---
```
