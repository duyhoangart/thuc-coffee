"""Kiểm tra môi trường phát triển Thức Coffee.
Chạy:  python scripts/check_env.py
"""
import socket
import sqlite3
import ssl
import sys
import threading

results = []


def check(name, fn):
    try:
        detail = fn()
        results.append((name, True, detail or ""))
    except Exception as e:  # noqa: BLE001
        results.append((name, False, str(e)))


def python_version():
    v = sys.version_info
    if v < (3, 10):
        raise RuntimeError(f"Cần Python >= 3.10, đang dùng {v.major}.{v.minor}")
    return f"Python {v.major}.{v.minor}.{v.micro}"


def tkinter_ok():
    import tkinter
    return f"tkinter {tkinter.TkVersion}"


def sqlite_ok():
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE t(id INTEGER PRIMARY KEY, name TEXT)")
    con.execute("INSERT INTO t(name) VALUES ('Cà phê sữa')")
    row = con.execute("SELECT name FROM t").fetchone()
    con.close()
    assert row[0] == "Cà phê sữa"
    return f"SQLite {sqlite3.sqlite_version} (đọc/ghi tiếng Việt OK)"


def ssl_ok():
    ssl.create_default_context()
    return ssl.OPENSSL_VERSION


def socket_ok():
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    port = srv.getsockname()[1]

    def serve():
        conn, _ = srv.accept()
        conn.sendall(conn.recv(1024))
        conn.close()

    t = threading.Thread(target=serve, daemon=True)
    t.start()
    cli = socket.create_connection(("127.0.0.1", port), timeout=3)
    cli.sendall(b'{"type":"PING"}')
    data = cli.recv(1024)
    cli.close()
    srv.close()
    assert data == b'{"type":"PING"}'
    return f"TCP loopback echo OK (cổng thử {port})"


check("Phiên bản Python", python_version)
check("Giao diện Tkinter", tkinter_ok)
check("SQLite", sqlite_ok)
check("SSL/TLS (module ssl)", ssl_ok)
check("Socket TCP + threading", socket_ok)

width = max(len(n) for n, _, _ in results)
for name, ok, detail in results:
    print(f"[{'OK ' if ok else 'LỖI'}] {name.ljust(width)}  {detail}")
sys.exit(0 if all(ok for _, ok, _ in results) else 1)
