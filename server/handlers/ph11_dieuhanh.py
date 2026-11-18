"""PH11 - Điều hành chung (Chủ quán): doanh thu và tổng quan. Quản lý KHÔNG có quyền ở đây."""
import time

from protocol.constants import CHUQUAN, ORDER_COOKING, ORDER_WAIT_KITCHEN, ORDER_WAIT_SERVICE, PAY_PAID, RES_PENDING
from server.core import ServerError, handler

FORMATS = {"day": ("%Y-%m-%d", 14), "week": ("%Y-W%W", 12), "month": ("%Y-%m", 12)}


@handler("REVENUE", "PH11", [CHUQUAN])
def revenue(ctx, s, p):
    """Doanh thu gộp mọi ca theo ngày/tuần/tháng (FR-21)."""
    period = p.get("period", "day")
    if period not in FORMATS:
        raise ServerError("BAD_REQUEST", "Kỳ phải là day, week hoặc month")
    fmt, limit = FORMATS[period]
    rows = ctx.db.query(
        "SELECT strftime(?, o.paid_at,'unixepoch','localtime') AS label, COUNT(DISTINCT o.id) AS orders, "
        "SUM(oi.price*oi.quantity) AS revenue FROM orders o JOIN order_items oi ON oi.order_id=o.id "
        "WHERE o.payment_status=? GROUP BY label ORDER BY label DESC LIMIT ?", (fmt, PAY_PAID, limit))
    return {"rows": rows, "total": sum(r["revenue"] or 0 for r in rows)}


@handler("OVERVIEW", "PH11", [CHUQUAN])
def overview(ctx, s, p):
    db = ctx.db
    today = time.strftime("%Y-%m-%d")
    rev = db.one("SELECT COALESCE(SUM(oi.price*oi.quantity),0) r, COUNT(DISTINCT o.id) n FROM orders o "
                 "JOIN order_items oi ON oi.order_id=o.id WHERE o.payment_status=? AND "
                 "strftime('%Y-%m-%d', o.paid_at,'unixepoch','localtime')=?", (PAY_PAID, today))
    prog = db.one("SELECT COUNT(*) n FROM orders WHERE status IN (?,?,?)",
                  (ORDER_WAIT_SERVICE, ORDER_WAIT_KITCHEN, ORDER_COOKING))["n"]
    staff = db.one("SELECT COUNT(*) n FROM staff WHERE locked=0 AND role<>'ADMIN'")["n"]
    res = db.one("SELECT COUNT(*) n FROM reservations WHERE status=?", (RES_PENDING,))["n"]
    return {"rows": [{"key": "Doanh thu hôm nay (đ)", "value": rev["r"]},
                     {"key": "Số đơn đã thanh toán hôm nay", "value": rev["n"]},
                     {"key": "Đơn đang xử lý", "value": prog},
                     {"key": "Nhân viên đang hoạt động", "value": staff},
                     {"key": "Đặt bàn chờ xác nhận", "value": res}]}
