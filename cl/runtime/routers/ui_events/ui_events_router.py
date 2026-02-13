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
from cl.runtime.schema.type_info import TypeInfo
from cl.runtime.serializers.bootstrap_serializers import BootstrapSerializers
from cl.runtime.ui.control.control_key import ControlKey
from cl.runtime.ui.event.event_manager import EventManager

router = APIRouter()
log = logging.getLogger(__name__)
_ui_event_serializer = BootstrapSerializers.FOR_UI_EVENTS


@router.websocket(
    path="/control_events/",
)
async def dynamic_controls_websocket_endpoint(
    *,
    key: str = "",
    type: str = "",
    viewer_name: str = "",
    websocket: WebSocket,
    manager=Depends(get_ui_events_connection_manager),
) -> None:
    """
    Endpoint used for two-way communication with custom ui components (Ui Builder),
    allows frontend to update Controls persisted in database, and for the database
    to send update events to the frontend.
    """

    tenant_id = active(DataSource).tenant.tenant_id
    connection_id = f"{tenant_id};{key};{type};{viewer_name}"

    try:
        await manager.connect(connection_id, websocket)

        # trying to get the short name of the type to check if such a type exists, if not it will throw an error
        TypeInfo.from_type_name(type)

        root_control_key = ControlKey(view_for=key, view_name=viewer_name, control_path="root")
        root_node = active(DataSource).load_one_or_none(root_control_key.build())
        if root_node is None:
            raise RuntimeError("Root node is missing")

        event_manager = EventManager(root_node=root_node.clone())

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
