"""PH07 - Thanh toán & Công nợ (FR-05, 09, 10, 11)."""
import time

from protocol.constants import CHUQUAN, KHACH, PAY_METHODS, PAY_PAID, PAY_UNPAID, PHUCVU, THUNGAN
from server.core import ServerError, handler
from server.services import need, notify_order, order_full, order_row, to_int


@handler("PAYMENT_REQUEST", "PH07", [KHACH])
def payment_request(ctx, s, p):
    need(p, "order_id")
    o = order_full(ctx.db, to_int(p["order_id"], "Đơn"))
    if o["table_id"] != s.table_id:
        raise ServerError("FORBIDDEN", "Đây không phải đơn của bàn bạn")
    if o["payment_status"] == PAY_PAID:
        raise ServerError("BAD_STATE", "Đơn đã thanh toán")
    ctx.db.execute("UPDATE orders SET payment_requested=1 WHERE id=?", (o["id"],))
    o = notify_order(ctx, o["id"])
    ctx.push([THUNGAN], "PAYMENT_REQUESTED", order_row(o))
    return {}


@handler("PAYMENT_PENDING", "PH07", [THUNGAN, CHUQUAN])
def payment_pending(ctx, s, p):
    """Danh sách chờ thanh toán = công nợ. only_requested=True: chỉ đơn khách đã gửi yêu cầu."""
    sql = "SELECT id FROM orders WHERE payment_status=?"
    if p.get("only_requested"):
        sql += " AND payment_requested=1"
    ids = ctx.db.query(sql + " ORDER BY payment_requested DESC, id", (PAY_UNPAID,))
    rows = [order_row(order_full(ctx.db, r["id"])) for r in ids]
    return {"rows": rows, "total_debt": sum(r["total"] for r in rows)}


@handler("PAYMENT_CONFIRM", "PH07", [THUNGAN])
def payment_confirm(ctx, s, p):
    need(p, "order_id", "method")
    if p["method"] not in PAY_METHODS:
        raise ServerError("BAD_REQUEST", "Hình thức thanh toán không hợp lệ")
    o = order_full(ctx.db, to_int(p["order_id"], "Đơn"))
    if o["payment_status"] == PAY_PAID:
        raise ServerError("BAD_STATE", "Đơn đã thanh toán")
    ctx.db.execute("UPDATE orders SET payment_status=?, payment_method=?, paid_at=?, paid_by=? WHERE id=?",
                   (PAY_PAID, p["method"], time.time(), s.user_id, o["id"]))
    o = notify_order(ctx, o["id"])
    row = order_row(o)
    ctx.push([THUNGAN, CHUQUAN], "PAYMENT_DONE", row)
    return {"total": o["total"]}
