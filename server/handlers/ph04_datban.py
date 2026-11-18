"""PH04 - Đặt bàn & Tài khoản khách (FR-03, 18, 27-29, 31)."""
import re
import time

from database.security import hash_password, verify_password
from protocol.constants import (KHACH, QUANLY, RES_CANCEL, RES_NO, RES_OK, RES_PENDING)
from server.core import PUBLIC, ServerError, handler
from server.services import fmt_dt, need, to_int

MAX_PENDING = 3          # tối đa số yêu cầu đang chờ / khách
MAX_PER_HOUR = 5         # tối đa số yêu cầu tạo trong 1 giờ / khách (chống spam)
PHONE_RE = re.compile(r"^0\d{9}$")


def _need_customer(s):
    if s.customer_id is None:
        raise ServerError("NEED_LOGIN", "Cần đăng nhập tài khoản khách để đặt bàn")


@handler("CUSTOMER_REGISTER", "PH04", PUBLIC)
def customer_register(ctx, s, p):
    need(p, "phone", "full_name", "password")
    phone = str(p["phone"]).strip()
    if not PHONE_RE.match(phone):
        raise ServerError("BAD_REQUEST", "Số điện thoại phải gồm 10 chữ số, bắt đầu bằng 0")
    if len(p["password"]) < 6:
        raise ServerError("BAD_REQUEST", "Mật khẩu tối thiểu 6 ký tự")
    if ctx.db.one("SELECT 1 FROM customers WHERE phone=?", (phone,)):
        raise ServerError("DUPLICATE", "Số điện thoại này đã đăng ký")
    ctx.db.execute("INSERT INTO customers(phone,full_name,password_hash,created_at) VALUES(?,?,?,?)",
                   (phone, p["full_name"].strip(), hash_password(p["password"]), time.time()))
    return {}


@handler("CUSTOMER_LOGIN", "PH04", PUBLIC)
def customer_login(ctx, s, p):
    need(p, "phone", "password")
    c = ctx.db.one("SELECT * FROM customers WHERE phone=?", (str(p["phone"]).strip(),))
    if not c or not verify_password(p["password"], c["password_hash"]):
        raise ServerError("BAD_LOGIN", "Sai số điện thoại hoặc mật khẩu")
    if c["locked"]:
        raise ServerError("LOCKED", "Tài khoản đã bị khóa")
    s.role, s.customer_id, s.name = KHACH, c["id"], c["full_name"]
    return {"role": KHACH, "name": c["full_name"], "customer_id": c["id"]}


@handler("RESERVATION_CREATE", "PH04", [KHACH])
def reservation_create(ctx, s, p):
    _need_customer(s)
    need(p, "guests", "arrive_time")
    guests = to_int(p["guests"], "Số khách", 1, 50)
    try:
        arrive = time.mktime(time.strptime(p["arrive_time"].strip(), "%Y-%m-%d %H:%M"))
    except ValueError:
        raise ServerError("BAD_REQUEST", "Giờ đến phải có dạng YYYY-MM-DD HH:MM")
    if arrive < time.time():
        raise ServerError("BAD_REQUEST", "Giờ đến phải ở tương lai")
    db = ctx.db
    pending = db.one("SELECT COUNT(*) n FROM reservations WHERE customer_id=? AND status=?",
                     (s.customer_id, RES_PENDING))["n"]
    recent = db.one("SELECT COUNT(*) n FROM reservations WHERE customer_id=? AND created_at>?",
                    (s.customer_id, time.time() - 3600))["n"]
    if pending >= MAX_PENDING or recent >= MAX_PER_HOUR:
        raise ServerError("RATE_LIMIT", "Bạn đã gửi quá nhiều yêu cầu đặt bàn, vui lòng thử lại sau")
    rid = db.execute("INSERT INTO reservations(customer_id,guests,arrive_time,status,created_at) VALUES(?,?,?,?,?)",
                     (s.customer_id, guests, p["arrive_time"].strip(), RES_PENDING, time.time()))
    ctx.push([QUANLY], "RESERVATION_NEW", {"id": rid, "name": s.name})
    return {"id": rid, "status": RES_PENDING}


@handler("RESERVATION_CANCEL", "PH04", [KHACH])
def reservation_cancel(ctx, s, p):
    _need_customer(s)
    need(p, "id")
    r = ctx.db.one("SELECT * FROM reservations WHERE id=? AND customer_id=?", (int(p["id"]), s.customer_id))
    if not r:
        raise ServerError("NOT_FOUND", "Không tìm thấy đặt bàn của bạn")
    if r["status"] not in (RES_PENDING, RES_OK):
        raise ServerError("BAD_STATE", f"Không thể hủy đặt bàn đang ở trạng thái '{r['status']}'")
    ctx.db.execute("UPDATE reservations SET status=? WHERE id=?", (RES_CANCEL, r["id"]))
    ctx.push([QUANLY], "RESERVATION_NEW", {"id": r["id"], "name": s.name})
    return {}


@handler("RESERVATION_MY", "PH04", [KHACH])
def reservation_my(ctx, s, p):
    _need_customer(s)
    rows = ctx.db.query("SELECT id, guests, arrive_time, status, created_at FROM reservations "
                        "WHERE customer_id=? ORDER BY id DESC", (s.customer_id,))
    for r in rows:
        r["created"] = fmt_dt(r["created_at"])
    return {"rows": rows}


@handler("RESERVATION_LIST", "PH04", [QUANLY])
def reservation_list(ctx, s, p):
    rows = ctx.db.query(
        "SELECT r.id, c.full_name AS name, c.phone, r.guests, r.arrive_time, r.status, r.created_at "
        "FROM reservations r JOIN customers c ON c.id=r.customer_id ORDER BY (r.status=?) DESC, r.id DESC LIMIT 200",
        (RES_PENDING,))
    for r in rows:
        r["created"] = fmt_dt(r["created_at"])
    return {"rows": rows}


@handler("RESERVATION_DECIDE", "PH04", [QUANLY])
def reservation_decide(ctx, s, p):
    need(p, "id")
    r = ctx.db.one("SELECT * FROM reservations WHERE id=?", (int(p["id"]),))
    if not r:
        raise ServerError("NOT_FOUND", "Không tìm thấy đặt bàn")
    if r["status"] != RES_PENDING:
        raise ServerError("BAD_STATE", "Đặt bàn này đã được xử lý")
    new = RES_OK if p.get("accept") else RES_NO
    ctx.db.execute("UPDATE reservations SET status=?, decided_by=? WHERE id=?", (new, s.user_id, r["id"]))
    ctx.push([KHACH], "RESERVATION_UPDATED", {"id": r["id"], "status": new},
             where=lambda x: x.customer_id == r["customer_id"])
    return {"status": new}
