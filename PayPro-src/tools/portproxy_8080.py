# -*- coding: utf-8 -*-
"""8080 -> VM(192.168.99.100:8889) TCP 转发器，供 cpolar website 隧道使用"""
import socket, threading, sys

LISTEN = ("::", 8080)  # IPv6 dual-stack, 同时接受 IPv4 (V6ONLY=0)
TARGET = ("192.168.99.100", 8889)

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
        upstream = socket.create_connection(TARGET, timeout=5)
    except OSError:
        client.close()
        return
    threading.Thread(target=pipe, args=(client, upstream), daemon=True).start()
    threading.Thread(target=pipe, args=(upstream, client), daemon=True).start()

def main():
    srv = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    srv.bind(LISTEN)
    srv.listen(64)
    print("forwarding 127.0.0.1:8080 -> %s:%s" % TARGET, flush=True)
    while True:
        c, _ = srv.accept()
        threading.Thread(target=handle, args=(c,), daemon=True).start()

if __name__ == "__main__":
    main()
