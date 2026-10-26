import os
import msvcrt
import _overlapped

r, w = os.pipe()
r_handle = msvcrt.get_osfhandle(r)
w_handle = msvcrt.get_osfhandle(w)

os.write(w, b"hello")
ov = _overlapped.Overlapped(0)
try:
    ov.ReadFile(r_handle, 10)
    print("ov.ReadFile success, bytes:", ov.getresult())
except Exception as e:
    print("ReadFile error:", e)

os.close(r)
os.close(w)
