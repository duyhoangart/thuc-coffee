"""PH08 - Giám sát vận hành (Quản lý): công việc, đơn trễ, ngưỡng cảnh báo. KHÔNG có doanh thu."""
from protocol.constants import (ORDER_COOKING, ORDER_WAIT_KITCHEN, ORDER_WAIT_SERVICE, QUANLY, RES_PENDING)
from server.core import ServerError, handler
from server.services import late_items, need


@handler("DASH_SUMMARY", "PH08", [QUANLY])
def dash_summary(ctx, s, p):
    db = ctx.db
    st = (ORDER_WAIT_SERVICE, ORDER_WAIT_KITCHEN, ORDER_COOKING)
    n = db.one("SELECT COUNT(*) n FROM orders WHERE status IN (?,?,?)", st)["n"]
    late_orders = len({i["order_id"] for i in late_items(db)})
    pend = db.one("SELECT COUNT(*) n FROM reservations WHERE status=?", (RES_PENDING,))["n"]
    rows = [{"key": "Đơn đang xử lý", "value": n}, {"key": "Đơn đang trễ", "value": late_orders},
            {"key": "Đặt bàn chờ xác nhận", "value": pend},
            {"key": "Ngưỡng cảnh báo trễ (phút)", "value": db.get_setting("late_threshold_minutes")}]
    return {"rows": rows}


@handler("LATE_LIST", "PH08", [QUANLY])
def late_list(ctx, s, p):
    return {"rows": [{"order_id": i["order_id"], "table": i["table"], "name": i["name"],
                      "quantity": i["quantity"], "status": i["status"], "wait_min": i["wait_min"]}
                     for i in late_items(ctx.db)]}


@handler("LATE_CONFIG_SET", "PH08", [QUANLY])
def late_config_set(ctx, s, p):
    need(p, "minutes")
    try:
        m = float(p["minutes"])
    except (TypeError, ValueError):
        raise ServerError("BAD_REQUEST", "Ngưỡng phải là số")
    if not 0.1 <= m <= 240:
        raise ServerError("BAD_REQUEST", "Ngưỡng phải từ 0.1 đến 240 phút")
    ctx.db.set_setting("late_threshold_minutes", m)  # đọc lại ở lần quét kế tiếp, không cần khởi động lại
    return {"minutes": m}
