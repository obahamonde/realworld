from typing import List, Any

from starlette.websockets import WebSocket, WebSocketDisconnect

from pydantic import BaseModel, Field
from datetime import datetime

from uuid import uuid4

from enum import Enum

from fastapi import FastAPI

from fastapi.templating import Jinja2Templates


class Status(str, Enum):

    success = "success"

    info = "info"

    warning = "warning"

    error = "error"


class Notification(BaseModel):

    id: str = Field(default_factory=lambda: str(uuid4()))

    timestamp: str = Field(default_factory=datetime.now().isoformat)

    message: str = Field(...)

    sub: str = Field(...)

    status: Status = Field(default=Status.info)


t = Jinja2Templates(directory="templates")


app = FastAPI()


@app.get("/")
async def get():
    return t.TemplateResponse("index.html", {"request": {}})


class Notifier:
    def __init__(self):

        self.connections: List[WebSocket] = []

        self.generator = self.get_notification_generator()

    async def get_notification_generator(self):

        while True:

            message = yield

            await self._notify(message)

    async def push(self, msg: Any):
        await self.generator.asend(msg)

    async def connect(self, websocket: WebSocket):

        await websocket.accept()

        self.connections.append(websocket)

    def remove(self, websocket: WebSocket):

        self.connections.remove(websocket)

    async def _notify(self, message: str):

        living_connections = []

        while len(self.connections) > 0:

            # Looping like this is necessary in case a disconnection is handled

            # during await websocket.send_text(message)

            websocket = self.connections.pop()

            await websocket.send_text(message)

            living_connections.append(websocket)

        self.connections = living_connections


notifier = Notifier()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await notifier.connect(websocket)

    try:

        while True:

            data = await websocket.receive_text()

            await websocket.send_text(f"Message text was: {data}")

    except WebSocketDisconnect:

        notifier.remove(websocket)


@app.get("/push/{message}")
async def push_to_connected_websockets(message: str):

    await notifier.push(f"! Push notification: {message} !")


@app.on_event("startup")
async def startup():

    # Prime the push notification generator

    await notifier.generator.asend(None)
