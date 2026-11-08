"""Streaming responses, server-sent events and a WebSocket echo."""
import json
from typing import Annotated

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/stream", tags=["streaming"])

Count = Annotated[int, Query(ge=1, le=1000)]


@router.get("/count")
def count(n: Count = 5):
    """Plain-text stream: one number per line."""
    def generate():
        for i in range(1, n + 1):
            yield f"{i}\n"
    return StreamingResponse(generate(), media_type="text/plain")


@router.get("/sse")
def server_sent_events(n: Count = 3):
    """``text/event-stream``: each event is ``data: <json>`` followed by a blank line."""
    def generate():
        for i in range(n):
            yield f"data: {json.dumps({'tick': i})}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")


@router.websocket("/ws/echo")
async def websocket_echo(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            text = await websocket.receive_text()
            await websocket.send_text(f"echo: {text}")
    except WebSocketDisconnect:
        pass
