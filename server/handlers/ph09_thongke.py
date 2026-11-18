"""PH09 - Thống kê & Ca làm việc (Quản lý): món bán chạy, thời gian phục vụ, ca làm."""
import re

from protocol.constants import CHUQUAN, QUANLY, SHIFT_NAMES
from server.core import ServerError, handler
from server.services import need, to_int

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@handler("STATS_TOP_ITEMS", "PH09", [QUANLY, CHUQUAN])
def stats_top_items(ctx, s, p):
    rows = ctx.db.query(
        "SELECT oi.name, SUM(oi.quantity) AS quantity FROM order_items oi JOIN orders o ON o.id=oi.order_id "
        "GROUP BY oi.name ORDER BY quantity DESC, oi.name LIMIT 10")
    return {"rows": rows}


@handler("STATS_AVG_SERVICE", "PH09", [QUANLY])
def stats_avg_service(ctx, s, p):
    r = ctx.db.one("SELECT COUNT(*) n, AVG(done_at - sent_to_kitchen_at) a FROM orders "
                   "WHERE done_at IS NOT NULL AND sent_to_kitchen_at IS NOT NULL")
    avg = round(r["a"] / 60, 1) if r["a"] is not None else 0
    return {"rows": [{"key": "Số đơn đã làm xong", "value": r["n"]},
                     {"key": "Thời gian phục vụ trung bình (phút)", "value": avg}]}


@handler("STAFF_BASIC", "PH09", [QUANLY])
def staff_basic(ctx, s, p):
    return {"rows": ctx.db.query("SELECT id, full_name, role FROM staff WHERE locked=0 AND role<>'ADMIN' "
                                 "AND role<>'CHUQUAN' ORDER BY full_name")}


@handler("SHIFT_LIST", "PH09", [QUANLY])
def shift_list(ctx, s, p):
    d = p.get("date") or ""
    sql = ("SELECT sh.id, sh.work_date, sh.shift_name, st.full_name, st.role FROM shifts sh "
           "JOIN staff st ON st.id=sh.staff_id")
    rows = ctx.db.query(sql + " WHERE sh.work_date=? ORDER BY sh.shift_name, st.full_name", (d,)) if d else \
        ctx.db.query(sql + " ORDER BY sh.work_date DESC, sh.shift_name LIMIT 200")
    return {"rows": rows}


def _check_shift(p):
    need(p, "date", "shift_name")
    if not DATE_RE.match(p["date"]):
        raise ServerError("BAD_REQUEST", "Ngày phải có dạng YYYY-MM-DD")
    if p["shift_name"] not in SHIFT_NAMES:
        raise ServerError("BAD_REQUEST", "Ca phải là Sáng, Chiều hoặc Tối")


@handler("SHIFT_ASSIGN", "PH09", [QUANLY])
def shift_assign(ctx, s, p):
    need(p, "staff_id")
    _check_shift(p)
    sid = to_int(p["staff_id"], "Nhân viên")
    if not ctx.db.one("SELECT 1 FROM staff WHERE id=? AND locked=0", (sid,)):
        raise ServerError("NOT_FOUND", "Không tìm thấy nhân viên")
    try:
        ctx.db.execute("INSERT INTO shifts(staff_id,work_date,shift_name) VALUES(?,?,?)",
                       (sid, p["date"], p["shift_name"]))
    except Exception:  # noqa: BLE001  (UNIQUE)
        raise ServerError("DUPLICATE", "Nhân viên đã có ca này")
    return {}


@handler("SHIFT_UPDATE", "PH09", [QUANLY])
def shift_update(ctx, s, p):
    need(p, "id", "date", "shift_name")
    _check_shift(p)
    try:
        ctx.db.execute("UPDATE shifts SET work_date=?, shift_name=? WHERE id=?", (p["date"], p["shift_name"], int(p["id"])))
    except Exception:  # noqa: BLE001
        raise ServerError("DUPLICATE", "Nhân viên đã có ca này")
    return {}


@handler("SHIFT_DELETE", "PH09", [QUANLY])
def shift_delete(ctx, s, p):
    need(p, "id")
    ctx.db.execute("DELETE FROM shifts WHERE id=?", (int(p["id"]),))
    return {}
