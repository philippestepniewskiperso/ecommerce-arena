"""In-process WebSocket room manager for live chat."""
from collections import defaultdict
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # ticket_id → list of (ws, sender_type, display_name)
        self._rooms: dict[str, list[tuple[WebSocket, str, str]]] = defaultdict(list)

    async def connect(self, ticket_id: str, ws: WebSocket, sender_type: str, display_name: str):
        await ws.accept()
        self._rooms[ticket_id].append((ws, sender_type, display_name))

    def disconnect(self, ticket_id: str, ws: WebSocket):
        self._rooms[ticket_id] = [
            (w, t, n) for w, t, n in self._rooms[ticket_id] if w is not ws
        ]

    async def broadcast(self, ticket_id: str, data: dict):
        dead = []
        for ws, _, _ in list(self._rooms[ticket_id]):
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ticket_id, ws)

    def staff_connected(self, ticket_id: str) -> bool:
        return any(t == "staff" for _, t, _ in self._rooms[ticket_id])


manager = ConnectionManager()
