import os
import msvcrt
import asyncio
import asyncio.proactor_events as pe

class PipeReader:
    def __init__(self, fd):
        self._fd = fd
        self._handle = msvcrt.get_osfhandle(fd)
    def fileno(self):
        return self._handle
    def setblocking(self, val):
        pass
    def close(self):
        if self._fd is not None:
            try:
                os.close(self._fd)
            except Exception:
                pass
            self._fd = None

class PipeWriter:
    def __init__(self, fd):
        self._fd = fd
    def fileno(self):
        return self._fd
    def send(self, data):
        if self._fd is not None:
            return os.write(self._fd, data)
        return 0
    def setblocking(self, val):
        pass
    def close(self):
        if self._fd is not None:
            try:
                os.close(self._fd)
            except Exception:
                pass
            self._fd = None

def pipe_self_pipe(self):
    r, w = os.pipe()
    self._ssock = PipeReader(r)
    self._csock = PipeWriter(w)
    self._internal_fds += 1

pe.BaseProactorEventLoop._make_self_pipe = pipe_self_pipe

async def test_async():
    await asyncio.sleep(0.01)
    return "SUCCESS!"

res = asyncio.run(test_async())
print("Result:", res)
