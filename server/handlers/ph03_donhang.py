"""PH03 - Đặt món & Đơn hàng (khách): chọn món, gửi yêu cầu cho phục vụ, theo dõi đơn."""
import time

from protocol.constants import KHACH, ORDER_WAIT_SERVICE, PAY_PAID, PHUCVU
from server.core import ServerError, handler
from server.services import need, notify_order, order_full, order_row, to_int


@handler("ORDER_REQUEST", "PH03", [KHACH])
def order_request(ctx, s, p):
    """Khách gửi yêu cầu chọn món cho nhân viên phục vụ (không gửi thẳng cho bếp)."""
    if s.table_id is None:
        raise ServerError("FORBIDDEN", "Cần chọn bàn trước khi gọi món")
    items = p.get("items") or []
    if not items:
        raise ServerError("BAD_REQUEST", "Chưa chọn món nào")
    db = ctx.db
    prepared = []
    for it in items:
        qty = to_int(it.get("quantity"), "Số lượng", 1, 50)
        m = db.one("SELECT * FROM menu_items WHERE id=? AND active=1", (to_int(it.get("menu_item_id"), "Món", 1),))
        if not m:
            raise ServerError("NOT_FOUND", "Món không tồn tại")
        if not m["available"]:
            raise ServerError("UNAVAILABLE", f"{m['name']} đã hết hàng")
        prepared.append((m, qty, (it.get("note") or "")[:200]))
    oid = db.execute("INSERT INTO orders(table_id,customer_id,status,created_at) VALUES(?,?,?,?)",
                     (s.table_id, s.customer_id, ORDER_WAIT_SERVICE, time.time()))
    for m, qty, note in prepared:
        db.execute("INSERT INTO order_items(order_id,menu_item_id,name,price,quantity,note) VALUES(?,?,?,?,?,?)",
                   (oid, m["id"], m["name"], m["price"], qty, note))
    o = order_full(db, oid)
    ctx.push([PHUCVU], "SERVICE_REQUEST_NEW", order_row(o))
    return {"order_id": oid, "total": o["total"]}


@handler("ORDER_MY", "PH03", [KHACH])
def order_my(ctx, s, p):
    """Các món của bàn mình chưa thanh toán (FR-04)."""
    if s.table_id is None:
        return {"rows": []}
    orders = ctx.db.query("SELECT id FROM orders WHERE table_id=? AND payment_status<>? ORDER BY id DESC",
                          (s.table_id, PAY_PAID))
    rows = []
    for od in orders:
        o = order_full(ctx.db, od["id"])
        for i in o["items"]:
            rows.append({"order_id": o["id"], "name": i["name"], "quantity": i["quantity"], "note": i["note"],
                         "item_status": i["status"] if o["status"] != ORDER_WAIT_SERVICE else "Chờ phục vụ nhận",
                         "order_status": o["status"], "payment": o["payment_status"],
                         "requested": "Đã gửi" if o["payment_requested"] else ""})
    return {"rows": rows}


@handler("CALL_STAFF", "PH03", [KHACH])
def call_staff(ctx, s, p):
    if s.table_id is None:
        raise ServerError("FORBIDDEN", "Cần chọn bàn")
    ctx.push([PHUCVU], "STAFF_CALLED", {"table": f"Bàn {s.table_id}", "time": time.time()})
    return {}
