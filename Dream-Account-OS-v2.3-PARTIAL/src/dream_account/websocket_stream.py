from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass
from typing import Awaitable, Callable

import websockets


@dataclass
class StreamHealth:
    status: str = "DISCONNECTED"
    reconnects: int = 0
    last_message_ms: int | None = None
    stale_events: int = 0
    sequence_gaps: int = 0


class PublicStream:
    def __init__(self, uri: str, subscriptions: list[dict], decoder: Callable[[bytes | str], dict], reconcile: Callable[[], Awaitable[None]], stale_after: float = 15):
        self.uri, self.subscriptions, self.decoder, self.reconcile = uri, subscriptions, decoder, reconcile
        self.stale_after = stale_after
        self.health = StreamHealth()
        self._last_sequence: int | None = None

    async def run_once(self, on_message: Callable[[dict], Awaitable[None]], max_messages: int | None = None) -> None:
        self.health.status = "CONNECTING"
        async with websockets.connect(self.uri, ping_interval=10, ping_timeout=10, close_timeout=3) as ws:
            self.health.status = "CONNECTED"
            for subscription in self.subscriptions:
                await ws.send(json.dumps(subscription))
            await self.reconcile()
            count = 0
            while max_messages is None or count < max_messages:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=self.stale_after)
                except asyncio.TimeoutError:
                    self.health.stale_events += 1
                    self.health.status = "STALE"
                    raise
                message = self.decoder(raw)
                timestamp = int(message.get("ts", time.time() * 1000))
                if self.health.last_message_ms is not None and timestamp < self.health.last_message_ms:
                    raise ValueError("timestamp regression")
                sequence = message.get("sequence")
                if sequence is not None and self._last_sequence is not None and sequence != self._last_sequence + 1:
                    self.health.sequence_gaps += 1
                    await self.reconcile()
                self._last_sequence = sequence if sequence is not None else self._last_sequence
                self.health.last_message_ms = timestamp
                await on_message(message)
                count += 1

    async def run(self, on_message: Callable[[dict], Awaitable[None]]) -> None:
        delay = 1.0
        while True:
            try:
                await self.run_once(on_message)
                delay = 1.0
            except Exception:
                self.health.status = "RECONNECTING"
                self.health.reconnects += 1
                await asyncio.sleep(delay)
                delay = min(30.0, delay * 2)

