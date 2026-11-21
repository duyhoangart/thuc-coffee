"""PH02 - Quản lý thực đơn (FR-01, FR-15)."""
from protocol.constants import QUANLY
from server.core import ANY, ServerError, handler
from server.services import need, to_int


def _menu_rows(db):
    rows = db.query("SELECT id,name,description,price,category,available FROM menu_items WHERE active=1 "
                    "ORDER BY category, name")
    for r in rows:
        r["state"] = "Còn" if r["available"] else "Hết"
    return rows


def _changed(ctx):
    ctx.push(None, "MENU_UPDATED", {})


@handler("MENU_LIST", "PH02", ANY)
def menu_list(ctx, s, p):
    return {"rows": _menu_rows(ctx.db)}


@handler("MENU_ADD", "PH02", [QUANLY])
def menu_add(ctx, s, p):
    need(p, "name", "price")
    price = to_int(p["price"], "Giá", 0)
    ctx.db.execute("INSERT INTO menu_items(name,description,price,category) VALUES(?,?,?,?)",
                   (p["name"].strip(), p.get("description", ""), price, p.get("category") or "Khác"))
    _changed(ctx)
    return {}


@handler("MENU_UPDATE", "PH02", [QUANLY])
def menu_update(ctx, s, p):
    need(p, "id", "name", "price")
    price = to_int(p["price"], "Giá", 0)
    ctx.db.execute("UPDATE menu_items SET name=?, description=?, price=?, category=? WHERE id=? AND active=1",
                   (p["name"].strip(), p.get("description", ""), price, p.get("category") or "Khác", int(p["id"])))
    _changed(ctx)
    return {}


@handler("MENU_DELETE", "PH02", [QUANLY])
def menu_delete(ctx, s, p):
    need(p, "id")
    ctx.db.execute("UPDATE menu_items SET active=0 WHERE id=?", (int(p["id"]),))  # xóa mềm để giữ lịch sử đơn
    _changed(ctx)
    return {}


@handler("MENU_SET_PRICE", "PH02", [QUANLY])
def menu_set_price(ctx, s, p):
    need(p, "id", "price")
    ctx.db.execute("UPDATE menu_items SET price=? WHERE id=?", (to_int(p["price"], "Giá", 0), int(p["id"])))
    _changed(ctx)
    return {}


@handler("MENU_SET_AVAILABLE", "PH02", [QUANLY])
def menu_set_available(ctx, s, p):
    need(p, "id")
    ctx.db.execute("UPDATE menu_items SET available=? WHERE id=?", (1 if p.get("available", True) else 0, int(p["id"])))
    _changed(ctx)
    return {}
# Phụ trách: Ngân (Controller nghiệp vụ) - xử lý nghiệp vụ thực đơn