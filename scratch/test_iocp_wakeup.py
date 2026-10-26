import asyncio
import signal
import _overlapped
import asyncio.proactor_events as pe
from concurrent.futures import ThreadPoolExecutor

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

async def run_server():
    loop = asyncio.get_running_loop()
    fut = loop.create_future()
    def from_thread():
        loop.call_soon_threadsafe(fut.set_result, "THREADSAFE SUCCESS!")
    with ThreadPoolExecutor(1) as ex:
        ex.submit(from_thread)
    return await fut

res2 = asyncio.run(run_server())
print("Result 2:", res2)
