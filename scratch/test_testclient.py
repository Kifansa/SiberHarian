import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import asyncio
import signal
import _overlapped
import asyncio.proactor_events as pe
from fastapi.testclient import TestClient

signal.set_wakeup_fd = lambda fd, *a, **kw: -1

class DummySocket:
    def fileno(self):
        return -1
    def setblocking(self, val):
        pass
    def close(self):
        pass

def dummy_make_self_pipe(self):
    self._ssock = DummySocket()
    self._csock = DummySocket()
    self._internal_fds += 1

def dummy_close_self_pipe(self):
    pass

def dummy_loop_self_reading(self, f=None):
    pass

def iocp_write_to_self(self):
    if hasattr(self, '_proactor') and hasattr(self._proactor, '_iocp') and self._proactor._iocp:
        try:
            pro = self._proactor
            ov = _overlapped.Overlapped(0)
            f = self.create_future()
            pro._cache[ov.address] = (f, ov, None, lambda f, ov, obj: None)
            _overlapped.PostQueuedCompletionStatus(pro._iocp, 1, 0, ov.address)
        except Exception:
            pass

pe.BaseProactorEventLoop._make_self_pipe = dummy_make_self_pipe
pe.BaseProactorEventLoop._close_self_pipe = dummy_close_self_pipe
pe.BaseProactorEventLoop._loop_self_reading = dummy_loop_self_reading
pe.BaseProactorEventLoop._write_to_self = iocp_write_to_self

from src.web.app import app
client = TestClient(app)
resp = client.get("/api/statistik-publik")
print("Response status:", resp.status_code)
print("Data keys:", list(resp.json().keys()))
