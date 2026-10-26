import sys, os
sys.path.insert(0, os.path.abspath("."))
print("Line 3: starting imports...", flush=True)
import asyncio
import time
print("Line 6: importing ambil_tren...", flush=True)
from src.web.app import ambil_tren
print("Line 8: imported ambil_tren!", flush=True)

async def main():
    print("Inside main, calling ambil_tren()...", flush=True)
    t0 = time.time()
    res = await ambil_tren()
    print("ambil_tren returned status:", res.get("status"), "in", round(time.time() - t0, 3), "seconds", flush=True)

if __name__ == "__main__":
    print("Starting asyncio.run...", flush=True)
    asyncio.run(main())
