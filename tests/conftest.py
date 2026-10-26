import sys
import signal
import pytest
from unittest.mock import MagicMock
import google.generativeai as genai

# 1. Patch asyncio ProactorEventLoop self-pipe for Windows sandbox
if sys.platform == "win32":
    import asyncio.proactor_events as pe
    import _overlapped

    try:
        signal.set_wakeup_fd = lambda fd, *a, **kw: -1
    except Exception:
        pass

    class _DummySocket:
        def fileno(self):
            return -1
        def setblocking(self, val):
            pass
        def close(self):
            pass

    def _dummy_make_self_pipe(self):
        self._ssock = _DummySocket()
        self._csock = _DummySocket()
        self._internal_fds += 1

    def _dummy_close_self_pipe(self):
        pass

    def _dummy_loop_self_reading(self, f=None):
        pass

    def _iocp_write_to_self(self):
        if hasattr(self, "_proactor") and hasattr(self._proactor, "_iocp") and self._proactor._iocp:
            try:
                pro = self._proactor
                ov = _overlapped.Overlapped(0)
                f = self.create_future()
                pro._cache[ov.address] = (f, ov, None, lambda f, ov, obj: None)
                _overlapped.PostQueuedCompletionStatus(pro._iocp, 1, 0, ov.address)
            except Exception:
                pass

    pe.BaseProactorEventLoop._make_self_pipe = _dummy_make_self_pipe
    pe.BaseProactorEventLoop._close_self_pipe = _dummy_close_self_pipe
    pe.BaseProactorEventLoop._loop_self_reading = _dummy_loop_self_reading
    pe.BaseProactorEventLoop._write_to_self = _iocp_write_to_self


# 2. 100% OFFLINE Mock for google.generativeai
class _MockContentResponse:
    def __init__(self, text=""):
        self.text = text

def _mock_generate_content(self, contents, *args, **kwargs):
    content_str = str(contents)
    if "JSON array" in content_str or "ART-" in content_str:
        return _MockContentResponse('[{"id": "ART-1", "kategori": "insiden_spesifik"}]')
    return _MockContentResponse("Analisis intelijen siber narasi terverifikasi.")

class _MockModelMeta:
    def __init__(self, name):
        self.name = name
        self.supported_generation_methods = ["generateContent"]

def _mock_list_models(*args, **kwargs):
    models = [
        "models/gemini-2.5-flash",
        "models/gemini-2.5-flash-lite",
        "models/gemini-3-flash",
        "models/gemini-3.1-flash-lite",
        "models/gemini-3.6-flash",
        "models/gemini-3.5-flash-lite",
        "models/gemini-3.8-flash",
        "models/gemini-embedding-001",
        "models/gemini-embedding-exp-03-07",
        "models/text-embedding-004",
    ]
    return [_MockModelMeta(m) for m in models]

def _mock_embed_content(*args, **kwargs):
    from src.cti.vector_store import compute_deterministic_embedding
    content = kwargs.get("content") or (args[1] if len(args) > 1 else "")
    if isinstance(content, list):
        return {"embedding": [compute_deterministic_embedding(str(c)) for c in content]}
    return {"embedding": compute_deterministic_embedding(str(content))}

genai.GenerativeModel.generate_content = _mock_generate_content
genai.list_models = _mock_list_models
genai.embed_content = _mock_embed_content
