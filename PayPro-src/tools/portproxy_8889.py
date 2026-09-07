import socket, threading, sys

VM_HOST, VM_PORT = "192.168.99.100", 8889
LISTEN_HOST, LISTEN_PORT = "127.0.0.1", 8889

def pipe(a, b):
    try:
        while True:
            data = a.recv(65536)
            if not data:
                break
            b.sendall(data)
    except OSError:
        pass
    finally:
        try: a.close()
        except OSError: pass
        try: b.close()
        except OSError: pass

def handle(client):
    try:
        upstream = socket.create_connection((VM_HOST, VM_PORT), timeout=10)
    except OSError as e:
        print(f"[ERR] upstream {VM_HOST}:{VM_PORT} -> {e}", flush=True)
        client.close()
        return
    threading.Thread(target=pipe, args=(client, upstream), daemon=True).start()
    threading.Thread(target=pipe, args=(upstream, client), daemon=True).start()

srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
srv.bind((LISTEN_HOST, LISTEN_PORT))
srv.listen(64)
print(f"[OK] forwarding {LISTEN_HOST}:{LISTEN_PORT} -> {VM_HOST}:{VM_PORT}", flush=True)
while True:
    c, _ = srv.accept()
    threading.Thread(target=handle, args=(c,), daemon=True).start()
