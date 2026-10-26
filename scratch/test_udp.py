import socket

s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s1.bind(("127.0.0.1", 0))
port = s1.getsockname()[1]
print("UDP Bound to 127.0.0.1:", port)

s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s2.sendto(b"hello", ("127.0.0.1", port))
    data, addr = s1.recvfrom(1024)
    print("UDP Received:", data, "from", addr)
except Exception as e:
    print("UDP failed:", e)
finally:
    s1.close()
    s2.close()
