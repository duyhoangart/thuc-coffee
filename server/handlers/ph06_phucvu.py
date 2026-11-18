"""PH06 - Phục vụ: nhận yêu cầu của khách, chuyển đơn cho bếp, theo dõi món/bàn/thanh toán."""
import time

from protocol.constants import (ORDER_WAIT_KITCHEN, ORDER_WAIT_SERVICE, PAY_PAID, PAY_UNPAID, PHACHE, PHUCVU)
from server.core import ServerError, handler
from server.services import need, notify_order, order_full, order_row, to_int


@handler("SERVICE_REQUESTS", "PH06", [PHUCVU])
def service_requests(ctx, s, p):
    ids = ctx.db.query("SELECT id FROM orders WHERE status=? ORDER BY id", (ORDER_WAIT_SERVICE,))
    return {"rows": [order_row(order_full(ctx.db, r["id"])) for r in ids]}


@handler("ORDER_FORWARD", "PH06", [PHUCVU])
def order_forward(ctx, s, p):
    need(p, "order_id")
    oid = to_int(p["order_id"], "Đơn")
    o = order_full(ctx.db, oid)
    if o["status"] != ORDER_WAIT_SERVICE:
        raise ServerError("BAD_STATE", "Đơn này đã được chuyển cho bếp")
    ctx.db.execute("UPDATE orders SET status=?, sent_to_kitchen_at=? WHERE id=?",
                   (ORDER_WAIT_KITCHEN, time.time(), oid))
    o = notify_order(ctx, oid)
    ctx.push([PHACHE], "KITCHEN_NEW_ORDER", order_row(o))
    return {}


@handler("SERVICE_TABLES", "PH06", [PHUCVU])
def service_tables(ctx, s, p):
    rows = []
    for t in ctx.db.query("SELECT id, name FROM tables_cafe ORDER BY id"):
        orders = ctx.db.query("SELECT id,status,payment_status FROM orders WHERE table_id=? AND payment_status=? "
                              "ORDER BY id", (t["id"], PAY_UNPAID))
        rows.append({"table": t["name"], "orders": len(orders),
                     "status": ", ".join(sorted({o["status"] for o in orders})) or "Trống",
                     "payment": PAY_UNPAID if orders else ""})
    return {"rows": rows}


@handler("PAYMENT_STATUS_LIST", "PH06", [PHUCVU])
def payment_status_list(ctx, s, p):
    """Phục vụ kiểm tra đơn đã thanh toán chưa (đơn chưa thanh toán + 20 đơn thanh toán gần nhất)."""
    ids = ctx.db.query("SELECT id FROM orders WHERE payment_status=? ORDER BY id", (PAY_UNPAID,))
    ids += ctx.db.query("SELECT id FROM orders WHERE payment_status=? ORDER BY paid_at DESC LIMIT 20", (PAY_PAID,))
    return {"rows": [order_row(order_full(ctx.db, r["id"])) for r in ids]}
