"""Shared fixture: compile a harness config for the host platform, run the
resulting binary, and hand the test an aioesphomeapi client connected to it.

The harness binary is a full ESPHome runtime (template sensors, scripts,
automations, native API server) running as a plain Linux process — the same
mechanism ESPHome core uses for its own integration tests.
"""

from __future__ import annotations

import asyncio
import math
import socket
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import pytest_asyncio
from aioesphomeapi import APIClient, EntityState

TESTS_DIR = Path(__file__).resolve().parent.parent
HARNESS_DIR = TESTS_DIR / "harness"
API_PORT = 6053
DEFAULT_TIMEOUT = 5.0


def _compile(config: Path) -> Path:
    """Compile a harness config and return the path to the host binary.

    ESPHome's own build cache makes recompiles a no-op, so this is cheap
    for every test after the first.
    """
    subprocess.run(
        ["esphome", "compile", str(config)],
        check=True,
        capture_output=True,
        text=True,
        cwd=config.parent,
    )
    name = config.stem.replace("_", "-")
    binary = config.parent / ".esphome" / "build" / f"t-{name}" / ".pioenvs" / f"t-{name}" / "program"
    assert binary.exists(), f"compiled binary not found at {binary}"
    return binary


@dataclass
class Harness:
    client: APIClient
    states: dict[str, EntityState] = field(default_factory=dict)
    _entities: dict[str, object] = field(default_factory=dict)
    _services: dict[str, object] = field(default_factory=dict)
    _changed: asyncio.Event = field(default_factory=asyncio.Event)

    async def start(self) -> None:
        await self.client.connect(login=True)
        entities, services = await self.client.list_entities_services()
        self._entities = {e.object_id: e for e in entities}
        self._keys = {e.key: e.object_id for e in entities}
        self._services = {s.name: s for s in services}
        self.client.subscribe_states(self._on_state)

    def _on_state(self, state: EntityState) -> None:
        object_id = self._keys.get(state.key)
        if object_id is not None:
            self.states[object_id] = state
            self._changed.set()

    async def call(self, action: str, **kwargs) -> None:
        """Invoke an api action defined in the harness yaml."""
        await self.client.execute_service(self._services[action], kwargs)

    async def wait_for(self, object_id: str, predicate, timeout: float = DEFAULT_TIMEOUT):
        """Wait until the entity's state satisfies predicate; return the state."""
        async with asyncio.timeout(timeout):
            while True:
                state = self.states.get(object_id)
                if state is not None and predicate(state):
                    return state
                self._changed.clear()
                await self._changed.wait()

    async def wait_for_value(self, object_id: str, value, abs_tol: float = 1e-3, timeout: float = DEFAULT_TIMEOUT):
        """Wait until a sensor reports `value` (NaN-aware float compare)."""

        def matches(state) -> bool:
            got = state.state
            if isinstance(value, float) and math.isnan(value):
                return isinstance(got, float) and math.isnan(got)
            if isinstance(got, float) and isinstance(value, (int, float)):
                return math.isclose(got, value, abs_tol=abs_tol)
            return got == value

        return await self.wait_for(object_id, matches, timeout)


@pytest_asyncio.fixture
async def run_harness():
    """Factory fixture: `harness = await run_harness("failover_sensor")`."""
    processes: list[subprocess.Popen] = []
    clients: list[APIClient] = []

    async def _run(name: str) -> Harness:
        binary = await asyncio.to_thread(_compile, HARNESS_DIR / f"{name}.yaml")
        proc = subprocess.Popen([str(binary)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        processes.append(proc)
        # Wait for the API server to accept connections.
        async with asyncio.timeout(10):
            while True:
                try:
                    reader, writer = await asyncio.open_connection("127.0.0.1", API_PORT)
                    writer.close()
                    break
                except OSError:
                    await asyncio.sleep(0.05)
        client = APIClient("127.0.0.1", API_PORT, password=None)
        clients.append(client)
        harness = Harness(client=client)
        await harness.start()
        return harness

    yield _run

    for client in clients:
        await client.disconnect()
    for proc in processes:
        proc.terminate()
        proc.wait(timeout=5)
