"""Hàm dùng chung cho các handler: định dạng, tải đơn, thông báo."""
import time

from protocol.constants import (ITEM_DONE, ITEM_DOING, ORDER_COOKING, ORDER_READY, ORDER_WAIT_KITCHEN,
                                PHUCVU, QUANLY, KHACH)
from server.core import ServerError


def fmt_time(ts):
    return time.strftime("%H:%M:%S", time.localtime(ts)) if ts else ""


def fmt_dt(ts):
    return time.strftime("%d/%m %H:%M", time.localtime(ts)) if ts else ""


def need(p, *keys):
    for k in keys:
        if p.get(k) in (None, ""):
            raise ServerError("BAD_REQUEST", f"Thiếu trường {k}")


def to_int(v, name, lo=None, hi=None):
    try:
        n = int(v)
    except (TypeError, ValueError):
        raise ServerError("BAD_REQUEST", f"{name} phải là số nguyên")
    if (lo is not None and n < lo) or (hi is not None and n > hi):
        raise ServerError("BAD_REQUEST", f"{name} không hợp lệ")
    return n


def order_full(db, order_id):
    o = db.one("SELECT * FROM orders WHERE id=?", (order_id,))
    if not o:
        raise ServerError("NOT_FOUND", "Không tìm thấy đơn")
    o["items"] = db.query("SELECT * FROM order_items WHERE order_id=? ORDER BY id", (order_id,))
    o["total"] = sum(i["price"] * i["quantity"] for i in o["items"])
    o["table"] = f"Bàn {o['table_id']}"
    return o


def items_text(o):
    return "; ".join(f"{i['quantity']}x {i['name']}" for i in o["items"])


def order_row(o):
    return {"order_id": o["id"], "table": o["table"], "items": items_text(o), "total": o["total"],
            "status": o["status"], "payment": o["payment_status"],
            "requested": "Có" if o["payment_requested"] else "", "method": o.get("payment_method") or "",
            "created": fmt_time(o["created_at"])}


def notify_order(ctx, order_id):
    """Đẩy trạng thái đơn tới khách của bàn đó, phục vụ và quản lý."""
    o = order_full(ctx.db, order_id)
    row = order_row(o)
    ctx.push([PHUCVU, QUANLY], "ORDER_UPDATED", row)
    ctx.push([KHACH], "ORDER_UPDATED", row, where=lambda s: s.table_id == o["table_id"])
    return o


def recompute_order_status(ctx, order_id):
    """Suy ra trạng thái đơn từ trạng thái các món (A7.3). Trả True nếu vừa xong hết."""
    db = ctx.db
    items = db.query("SELECT status FROM order_items WHERE order_id=?", (order_id,))
    st = [i["status"] for i in items]
    just_ready = False
    if st and all(x == ITEM_DONE for x in st):
        db.execute("UPDATE orders SET status=?, done_at=? WHERE id=?", (ORDER_READY, time.time(), order_id))
        ctx.alerted.pop(order_id, None)
        just_ready = True
    elif any(x in (ITEM_DOING, ITEM_DONE) for x in st):
        db.execute("UPDATE orders SET status=? WHERE id=?", (ORDER_COOKING, order_id))
    else:
        db.execute("UPDATE orders SET status=? WHERE id=?", (ORDER_WAIT_KITCHEN, order_id))
    return just_ready


def late_threshold_sec(db):
    try:
        return max(0.05, float(db.get_setting("late_threshold_minutes"))) * 60
    except (TypeError, ValueError):
        return 600


def late_items(db):
    """Các món chờ/đang làm quá ngưỡng (A8). Đọc ngưỡng mỗi lần gọi nên đổi là áp dụng ngay."""
    limit = late_threshold_sec(db)
    now = time.time()
    rows = db.query(
        "SELECT oi.id AS item_id, oi.order_id, oi.name, oi.quantity, oi.status, o.table_id, o.sent_to_kitchen_at "
        "FROM order_items oi JOIN orders o ON o.id=oi.order_id "
        "WHERE oi.status IN ('Chờ','Đang làm') AND o.sent_to_kitchen_at IS NOT NULL")
    out = []
    for r in rows:
        wait = now - r["sent_to_kitchen_at"]
        if wait > limit:
            r["wait_min"] = int(wait // 60)
            r["table"] = f"Bàn {r['table_id']}"
            out.append(r)
    return out
