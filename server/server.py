"""Server Thức Coffee: 2 cổng (LAN và Internet), heartbeat, quét đơn trễ."""
import json
import logging
import os
import socket
import ssl
import threading
import time

from database.db import Database
from protocol.constants import PHACHE, QUANLY
from server import core
from server.core import Context, serve_client
from server.services import late_items

# Import để các handler tự đăng ký
from server.handlers import (common, ph01_quantri, ph02_thucdon, ph03_donhang, ph04_datban,  # noqa: F401
                             ph05_phache, ph06_phucvu, ph07_thanhtoan, ph08_giamsat, ph09_thongke,
                             ph10_nhansu, ph11_dieuhanh)

log = logging.getLogger("thuccoffee")


def load_config(path=None):
    for p in ([path] if path else ["config/config.json", "config/config.example.json"]):
        if p and os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    raise FileNotFoundError("Không tìm thấy config/config.json hoặc config.example.json")


def _listener(ctx, port, channel, ssl_ctx=None):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((ctx.config["host"], port))
    srv.listen(64)
    log.info("Lắng nghe cổng %s (%s)%s", port, channel, " + SSL/TLS" if ssl_ctx else "")

    def accept_loop():
        while True:
            try:
                conn, addr = srv.accept()
            except OSError:
                return
            threading.Thread(target=_handle, args=(ctx, conn, addr, channel, ssl_ctx), daemon=True).start()

    threading.Thread(target=accept_loop, daemon=True, name=f"accept-{channel}").start()
    return srv


def _handle(ctx, conn, addr, channel, ssl_ctx):
    try:
        if ssl_ctx:
            conn.settimeout(10)
            conn = ssl_ctx.wrap_socket(conn, server_side=True)
            conn.settimeout(None)
    except (ssl.SSLError, OSError) as e:
        log.warning("Bắt tay SSL thất bại từ %s: %s", addr[0], e)
        conn.close()
        return
    serve_client(ctx, conn, addr, channel)


def _heartbeat_loop(ctx):
    while True:
        try:
            interval = max(1, int(ctx.db.get_setting("heartbeat_interval_sec")))
            timeout = max(interval + 1, int(ctx.db.get_setting("heartbeat_timeout_sec")))
        except (TypeError, ValueError):
            interval, timeout = 5, 15
        now = time.time()
        for s in list(ctx.sessions.values()):
            if now - s.last_seen > timeout:
                log.info("Session #%s quá hạn heartbeat, ngắt", s.id)
                s.close()
            else:
                s.push("PING", {})
        time.sleep(interval)


def _late_loop(ctx):
    """Quét món trễ; đọc ngưỡng mới mỗi lần nên đổi cấu hình là áp dụng ngay (FR-19)."""
    while True:
        try:
            by_order = {}
            for it in late_items(ctx.db):
                by_order.setdefault(it["order_id"], []).append(it)
            for oid, its in by_order.items():
                if oid in ctx.alerted:
                    continue
                ctx.alerted[oid] = time.time()
                ctx.push([PHACHE, QUANLY], "ALERT_LATE_ORDER", {
                    "order_id": oid, "table": its[0]["table"], "wait_min": max(i["wait_min"] for i in its),
                    "items": "; ".join(f"{i['quantity']}x {i['name']}" for i in its)})
        except Exception:  # noqa: BLE001
            log.exception("Lỗi quét đơn trễ")
            ctx.note_error("PH08")
        time.sleep(ctx.config.get("late_scan_sec", 5))


def build_ssl(config):
    cert, key = config.get("ssl_cert"), config.get("ssl_key")
    if config.get("ssl_enabled", True) and cert and key and os.path.exists(cert) and os.path.exists(key):
        c = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        c.load_cert_chain(cert, key)
        return c
    log.warning("Chưa có chứng chỉ SSL (%s): cổng Internet chạy KHÔNG mã hóa. Chỉ dùng để thử nghiệm.", cert)
    return None


def start(config=None, db=None):
    """Khởi động server, trả (ctx, hàm_dừng). Dùng cho cả run_server.py và test."""
    config = config or load_config()
    db = db or Database(config["db_path"])
    ctx = Context(db, config)
    ssl_ctx = build_ssl(config)
    config["_ssl_active"] = bool(ssl_ctx)
    socks = [_listener(ctx, config["port_lan"], "lan")]
    if config.get("port_internet"):
        socks.append(_listener(ctx, config["port_internet"], "internet", ssl_ctx))
    threading.Thread(target=_heartbeat_loop, args=(ctx,), daemon=True, name="heartbeat").start()
    threading.Thread(target=_late_loop, args=(ctx,), daemon=True, name="late-scan").start()

    def stop():
        for s in socks:
            s.close()
        for x in list(ctx.sessions.values()):
            x.close()

    return ctx, stop


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    ctx, stop = start()
    log.info("Server sẵn sàng. Nhấn Ctrl+C để dừng.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop()
