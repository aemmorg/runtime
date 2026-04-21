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

import logging
import orjson as json
from fastapi import APIRouter
from fastapi import Depends
from fastapi import WebSocket
from fastapi import WebSocketDisconnect
from cl.runtime.backend.dependencies.ui_events import get_ui_events_connection_manager
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.schema.type_hint import TypeHint
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.serializers.key_serializers import KeySerializers
from cl.runtime.ui.event.event_manager import EventManager
from cl.runtime.ui.resolver.control_target_resolver import ControlTargetResolver
from cl.runtime.ui.resolver.record_target_resolver import RecordTargetResolver

router = APIRouter()
log = logging.getLogger(__name__)
_ui_event_serializer = BootstrapSerializers.FOR_UI_EVENTS


@router.websocket(
    path="/events/",
)
async def ui_events_websocket_endpoint(
    *,
    key: str = "",
    type: str = "",
    viewer_name: str = "",
    websocket: WebSocket,
    manager=Depends(get_ui_events_connection_manager),
) -> None:
    """
    Universal WebSocket gateway for two-way communication between frontend and database.
    Supports Controls (when viewer_name is set) and InteractiveMixin records (when viewer_name is empty).
    """

    tenant_id = active(DataSource).tenant.tenant_id
    connection_id = f"{tenant_id};{key};{type};{viewer_name}"

    try:
        await manager.connect(connection_id, websocket)

        # Deserialize the key string into a KeyMixin object
        record_type = TypeInfo.from_type_name(type)
        key_type = record_type.get_key_type()
        key_obj = KeySerializers.DELIMITED.deserialize(key, TypeHint.for_type(key_type)).build()

        # Use ControlTargetResolver for viewer-based Controls, RecordTargetResolver for InteractiveMixin records
        if viewer_name:
            resolver = ControlTargetResolver(key=key_obj, viewer_name=viewer_name)
        else:
            resolver = RecordTargetResolver(key=key_obj, type_name=type)

        event_manager = EventManager(resolver=resolver)

        while True:
            data = await websocket.receive_text()
            events = event_manager.dispatch(json.loads(data))

            for event in events[::-1]:
                serialized_event = _ui_event_serializer.serialize(event)
                data = json.dumps(serialized_event)
                await manager.send_message(connection_id, data.decode())

    except WebSocketDisconnect:
        await manager.disconnect(connection_id, websocket)
    except Exception:
        log.exception("Error occurred during websocket connection")
        await manager.disconnect(connection_id, websocket)
