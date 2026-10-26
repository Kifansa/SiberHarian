import os
import time
import _winapi
import asyncio
import asyncio.proactor_events as pe

_pipe_id = 0

def create_overlapped_pipe_pair():
    global _pipe_id
    _pipe_id += 1
    pipename = rf"\\.\pipe\asyncio_self_pipe_{os.getpid()}_{_pipe_id}_{int(time.time()*1000)}"
    
    h_read = _winapi.CreateNamedPipe(
        pipename,
        _winapi.PIPE_ACCESS_INBOUND | _winapi.FILE_FLAG_OVERLAPPED,
        _winapi.PIPE_WAIT,
        1, 4096, 4096, 0, _winapi.NULL
    )
    
    h_write = _winapi.CreateFile(
        pipename,
        _winapi.GENERIC_WRITE,
        0, _winapi.NULL,
        _winapi.OPEN_EXISTING,
        _winapi.FILE_FLAG_OVERLAPPED,
        _winapi.NULL
    )
    return h_read, h_write

class NamedPipeReader:
    def __init__(self, handle):
        self._handle = handle
    def fileno(self):
        return self._handle
    def setblocking(self, val):
        pass
    def close(self):
        if self._handle is not None:
            try:
                _winapi.CloseHandle(self._handle)
            except Exception:
                pass
            self._handle = None

class NamedPipeWriter:
    def __init__(self, handle):
        self._handle = handle
    def fileno(self):
        return self._handle
    def send(self, data):
        if self._handle is not None:
            ov = _winapi.Overlapped(0)
            try:
                _winapi.WriteFile(self._handle, data, ov)
            except Exception:
                pass
        return len(data)
    def setblocking(self, val):
        pass
    def close(self):
        if self._handle is not None:
            try:
                _winapi.CloseHandle(self._handle)
            except Exception:
                pass
            self._handle = None

def pipe_self_pipe(self):
    r, w = create_overlapped_pipe_pair()
    self._ssock = NamedPipeReader(r)
    self._csock = NamedPipeWriter(w)
    self._internal_fds += 1

pe.BaseProactorEventLoop._make_self_pipe = pipe_self_pipe

async def test_async():
    await asyncio.sleep(0.01)
    return "SUCCESS!"

res = asyncio.run(test_async())
print("Result:", res)
