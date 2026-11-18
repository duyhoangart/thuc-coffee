"""PH05 - Pha chế (Bếp): nhận đơn từ phục vụ, xử lý món, nhận cảnh báo trễ."""
import time

from protocol.constants import (ITEM_DOING, ITEM_DONE, ITEM_WAIT, ORDER_COOKING, ORDER_WAIT_KITCHEN,
                                PHACHE, PHUCVU)
from server.core import ServerError, handler
from server.services import (fmt_time, late_items, need, notify_order, recompute_order_status, to_int,
                             late_threshold_sec)


@handler("KITCHEN_LIST", "PH05", [PHACHE])
def kitchen_list(ctx, s, p):
    rows = ctx.db.query(
        "SELECT oi.id AS item_id, oi.order_id, oi.name, oi.quantity, oi.note, oi.status, o.table_id, "
        "o.sent_to_kitchen_at AS sent FROM order_items oi JOIN orders o ON o.id=oi.order_id "
        "WHERE o.status IN (?,?) AND oi.status IN (?,?) ORDER BY o.sent_to_kitchen_at, oi.id",
        (ORDER_WAIT_KITCHEN, ORDER_COOKING, ITEM_WAIT, ITEM_DOING))
    limit, now = late_threshold_sec(ctx.db), time.time()
    for r in rows:
        r["table"] = f"Bàn {r['table_id']}"
        r["received"] = fmt_time(r["sent"])
        wait = now - r["sent"]
        r["wait_min"] = int(wait // 60)
        r["late"] = "TRỄ" if wait > limit else ""
    return {"rows": rows}


def _change_item(ctx, item_id, expect, new):
    db = ctx.db
    it = db.one("SELECT * FROM order_items WHERE id=?", (item_id,))
    if not it:
        raise ServerError("NOT_FOUND", "Không tìm thấy món")
    if it["status"] != expect:
        raise ServerError("BAD_STATE", f"Món đang ở trạng thái '{it['status']}', không thể chuyển sang '{new}'")
    db.execute("UPDATE order_items SET status=? WHERE id=?", (new, item_id))
    ready = recompute_order_status(ctx, it["order_id"])
    o = notify_order(ctx, it["order_id"])
    ctx.push([PHACHE], "KITCHEN_REFRESH", {})
    if ready:
        ctx.push([PHUCVU], "ORDER_READY", {"order_id": o["id"], "table": o["table"]})
    return {}


@handler("ITEM_START", "PH05", [PHACHE])
def item_start(ctx, s, p):
    need(p, "item_id")
    return _change_item(ctx, to_int(p["item_id"], "Món"), ITEM_WAIT, ITEM_DOING)


@handler("ITEM_DONE", "PH05", [PHACHE])
def item_done(ctx, s, p):
    need(p, "item_id")
    return _change_item(ctx, to_int(p["item_id"], "Món"), ITEM_DOING, ITEM_DONE)
