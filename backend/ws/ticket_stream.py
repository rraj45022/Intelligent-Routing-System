from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

router = APIRouter(prefix="/ws", tags=["ws"])


class ConnectionManager:
	"""Lightweight WebSocket manager to broadcast ticket events."""

	def __init__(self) -> None:
		self.active_connections: List[WebSocket] = []

	async def connect(self, websocket: WebSocket) -> None:
		await websocket.accept()
		self.active_connections.append(websocket)

	def disconnect(self, websocket: WebSocket) -> None:
		if websocket in self.active_connections:
			self.active_connections.remove(websocket)

	async def broadcast(self, message: dict) -> None:
		# naive fan-out; for production consider background tasks and backpressure
		payload = jsonable_encoder(message)
		for connection in list(self.active_connections):
			try:
				await connection.send_json(payload)
			except Exception:
				self.disconnect(connection)


manager = ConnectionManager()


@router.websocket("/tickets")
async def ticket_stream(websocket: WebSocket):
	await manager.connect(websocket)
	try:
		while True:
			# keep the connection alive; we do not expect messages from the client
			await websocket.receive_text()
	except WebSocketDisconnect:
		manager.disconnect(websocket)


async def broadcast_ticket_event(event: dict) -> None:
	await manager.broadcast(event)
