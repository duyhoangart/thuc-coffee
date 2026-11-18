"""Lõi server: Session, đăng ký handler, phân quyền, điều phối message."""
import logging
import threading
import time
import traceback
from collections import deque

from protocol.messages import MessageStream

log = logging.getLogger("thuccoffee")

PUBLIC = None   # không cần đăng nhập
ANY = "*"       # mọi vai trò đã đăng nhập
HANDLERS = {}   # type -> (hàm, phân hệ, roles)

# Cổng Internet chỉ nhận các message này (FR-26, A3.6)
INTERNET_TYPES = {
    "CUSTOMER_REGISTER", "CUSTOMER_LOGIN", "RESERVATION_CREATE", "RESERVATION_CANCEL",
    "RESERVATION_MY", "SYNC_REQUEST",
}


class ServerError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def handler(msg_type, module, roles=ANY):
    """Đăng ký hàm xử lý cho một loại message thuộc một phân hệ."""
    def deco(fn):
        HANDLERS[msg_type] = (fn, module, roles)
        return fn
    return deco


class Session:
    _next = 1
    _lock = threading.Lock()

    def __init__(self, sock, addr, channel):
        with Session._lock:
            self.id = Session._next
            Session._next += 1
        self.sock = sock
        self.stream = MessageStream(sock)
        self.addr = addr
        self.ip = addr[0] if addr else "?"
        self.channel = channel          # "lan" | "internet"
        self.role = None
        self.user_id = None             # staff.id
        self.customer_id = None         # customers.id
        self.table_id = None            # khách tại quán
        self.name = ""
        self.connected_at = time.time()
        self.last_seen = time.time()
        self.alive = True

    def push(self, msg_type, payload=None, req_id=None):
        if not self.alive:
            return
        try:
            self.stream.send(msg_type, payload, req_id)
        except OSError:
            self.close()

    def close(self):
        self.alive = False
        try:
            self.sock.shutdown(2)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass


class Context:
    """Trạng thái dùng chung của server."""

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.sessions = {}
        self.lock = threading.RLock()
        self.started_at = time.time()
        self.rejected = deque(maxlen=200)       # yêu cầu bị từ chối (A3.5)
        self.blocked_ips = set()
        self.errors = {}                        # phân hệ -> deque thời điểm lỗi
        self.activity = {}                      # phân hệ -> lần hoạt động cuối
        self.alerted = {}                       # order_id -> thời điểm đã cảnh báo trễ

    # ---- quản lý session ----
    def add(self, s):
        with self.lock:
            self.sessions[s.id] = s

    def remove(self, s):
        with self.lock:
            self.sessions.pop(s.id, None)
        s.close()

    def online(self, roles=None, where=None):
        with self.lock:
            out = list(self.sessions.values())
        return [s for s in out if s.alive and s.role and (roles is None or s.role in roles)
                and (where is None or where(s))]

    def push(self, roles, msg_type, payload=None, where=None):
        for s in self.online(roles, where):
            s.push(msg_type, payload)

    def note_error(self, module):
        self.errors.setdefault(module, deque(maxlen=50)).append(time.time())

    def recent_errors(self, module, seconds=300):
        now = time.time()
        return sum(1 for t in self.errors.get(module, ()) if now - t <= seconds)


def dispatch(ctx, s, msg):
    t = msg.get("type")
    rid = msg.get("id")
    p = msg.get("payload") or {}
    if t == "PONG":
        return
    if t == "PING":
        s.push("PONG", {}, rid)
        return

    def reject(code, text):
        ctx.rejected.append({"time": time.time(), "ip": s.ip, "session": s.id, "role": s.role or "-",
                             "type": t, "code": code})
        s.push("ERROR", {"code": code, "message": text}, rid)

    entry = HANDLERS.get(t)
    if entry is None:
        return reject("UNKNOWN_TYPE", f"Không có loại message {t}")
    fn, module, roles = entry
    if s.channel == "internet" and t not in INTERNET_TYPES:
        return reject("FORBIDDEN", "Cổng Internet chỉ phục vụ đặt bàn")
    if roles is not PUBLIC:
        if s.role is None:
            return reject("NOT_LOGGED_IN", "Cần đăng nhập trước")
        if roles != ANY and s.role not in roles:
            return reject("FORBIDDEN", "Vai trò của bạn không có quyền thực hiện thao tác này")
    ctx.activity[module] = time.time()
    try:
        result = fn(ctx, s, p)
        s.push("ACK", result if result is not None else {}, rid)
    except ServerError as e:
        s.push("ERROR", {"code": e.code, "message": e.message}, rid)
    except Exception:  # noqa: BLE001
        log.error("Lỗi xử lý %s:\n%s", t, traceback.format_exc())
        ctx.note_error(module)
        s.push("ERROR", {"code": "INTERNAL", "message": "Lỗi hệ thống, vui lòng thử lại"}, rid)


def serve_client(ctx, sock, addr, channel):
    s = Session(sock, addr, channel)
    if s.ip in ctx.blocked_ips:
        s.close()
        return
    ctx.add(s)
    log.info("Kết nối #%s từ %s (%s)", s.id, s.ip, channel)
    try:
        while s.alive:
            msg = s.stream.recv()
            if msg is None:
                break
            s.last_seen = time.time()
            dispatch(ctx, s, msg)
    except (OSError, ValueError) as e:
        log.info("Ngắt #%s: %s", s.id, e)
    finally:
        ctx.remove(s)
        log.info("Đóng kết nối #%s", s.id)
