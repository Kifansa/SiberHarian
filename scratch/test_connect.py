import socket

for ip in ["127.0.0.1", "localhost", "0.0.0.0"]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((ip, 0))
        s.listen(1)
        port = s.getsockname()[1]
        print(f"Bound to {ip}:{port}")
        c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            c.connect((ip if ip != "0.0.0.0" else "127.0.0.1", port))
            print(f"Connected to {ip}:{port}!")
        except Exception as e:
            print(f"Connect failed for {ip}: {e}")
        finally:
            c.close()
    except Exception as e:
        print(f"Bind failed for {ip}: {e}")
    finally:
        s.close()
