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
from asyncio import gather
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect
from starlette.websockets import WebSocketState

log = logging.getLogger(__name__)


class ConnectionManager:
    """Manages websocket connections, connection data is stored in memory"""

    __instance = None

    @classmethod
    def instance(cls):
        """Returns the singleton instance of the ConnectionManager."""
        if cls.__instance is None:
            cls.__instance = ConnectionManager()
        return cls.__instance

    def __init__(self):
        """Initializes the ConnectionManager with an empty dictionary for active connections."""
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, connection_id: str, websocket: WebSocket):
        """Accept and keep track of the incoming connection."""
        # Accept the websocket connection if it's in the connecting state
        if websocket.client_state == WebSocketState.CONNECTING:
            await websocket.accept()
        # Add the websocket to the list of active connections for the given connection_id
        if connection_id in self.active_connections:
            self.active_connections[connection_id].append(websocket)
        else:
            self.active_connections[connection_id] = [websocket]

    async def disconnect(self, connection_id: str, websocket: WebSocket):
        """Forget the connection with connection_id."""
        try:
            await websocket.close()
        except Exception:
            pass

        if connections := self.active_connections.get(connection_id):

            # Remove the websocket from the list of active connections
            connections.remove(websocket) if websocket in connections else None

            # If there are no more websockets for the given connection_id, remove the entry
            if not connections:
                del self.active_connections[connection_id]

    async def send_message(self, connection_id: str, message: str):
        """Send provided message to websocket"""
        websockets = self.active_connections.get(connection_id, [])[:]  # Shallow copy
        if not websockets:
            return

        # Send the message to all websockets
        results: list = await gather(*(ws.send_text(message) for ws in websockets), return_exceptions=True)

        # Disconnect any websockets that failed to send the message
        for i, none_or_exception in enumerate(results):
            if none_or_exception is None:
                continue
            if not isinstance(none_or_exception, (RuntimeError, WebSocketDisconnect)):
                log.exception(none_or_exception)

            ws = websockets[i]
            await self.disconnect(connection_id, ws)
