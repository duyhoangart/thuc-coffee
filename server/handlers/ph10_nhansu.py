"""PH10 - Nhân sự & Tài khoản (Chủ quán): xem, thêm, khóa tài khoản, phân quyền vai trò (FR-22)."""
from database.security import hash_password
from protocol.constants import ASSIGNABLE_ROLES, CHUQUAN
from server.core import ServerError, handler
from server.services import need
import time


@handler("STAFF_LIST", "PH10", [CHUQUAN])
def staff_list(ctx, s, p):
    rows = ctx.db.query("SELECT id, username, full_name, role, locked FROM staff ORDER BY id")
    for r in rows:
        r["state"] = "Đã khóa" if r["locked"] else "Bình thường"
    return {"rows": rows}


@handler("STAFF_ADD", "PH10", [CHUQUAN])
def staff_add(ctx, s, p):
    need(p, "username", "password", "full_name", "role")
    if p["role"] not in ASSIGNABLE_ROLES:
        raise ServerError("BAD_REQUEST", "Vai trò không hợp lệ")
    if len(p["password"]) < 6:
        raise ServerError("BAD_REQUEST", "Mật khẩu tối thiểu 6 ký tự")
    if ctx.db.one("SELECT 1 FROM staff WHERE username=?", (p["username"].strip(),)):
        raise ServerError("DUPLICATE", "Tên đăng nhập đã tồn tại")
    ctx.db.execute("INSERT INTO staff(username,password_hash,full_name,role,created_at) VALUES(?,?,?,?,?)",
                   (p["username"].strip(), hash_password(p["password"]), p["full_name"].strip(), p["role"], time.time()))
    return {}


def _target(ctx, s, p):
    need(p, "id")
    t = ctx.db.one("SELECT * FROM staff WHERE id=?", (int(p["id"]),))
    if not t:
        raise ServerError("NOT_FOUND", "Không tìm thấy nhân viên")
    if t["id"] == s.user_id or t["role"] in ("CHUQUAN", "ADMIN"):
        raise ServerError("FORBIDDEN", "Không thể thay đổi tài khoản này")
    return t


@handler("STAFF_LOCK", "PH10", [CHUQUAN])
def staff_lock(ctx, s, p):
    t = _target(ctx, s, p)
    locked = 1 if p.get("locked", True) else 0
    ctx.db.execute("UPDATE staff SET locked=? WHERE id=?", (locked, t["id"]))
    if locked:
        for x in ctx.online(where=lambda x: x.user_id == t["id"]):
            x.push("FORCE_LOGOUT", {"reason": "Tài khoản đã bị khóa"})
            x.close()
    return {}


@handler("STAFF_SET_ROLE", "PH10", [CHUQUAN])
def staff_set_role(ctx, s, p):
    t = _target(ctx, s, p)
    need(p, "role")
    if p["role"] not in ASSIGNABLE_ROLES:
        raise ServerError("BAD_REQUEST", "Vai trò không hợp lệ")
    ctx.db.execute("UPDATE staff SET role=? WHERE id=?", (p["role"], t["id"]))
    for x in ctx.online(where=lambda x: x.user_id == t["id"]):
        x.push("FORCE_LOGOUT", {"reason": "Vai trò đã thay đổi, vui lòng đăng nhập lại"})
        x.close()
    return {}
