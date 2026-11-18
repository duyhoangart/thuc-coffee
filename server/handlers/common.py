"""Xác thực và đồng bộ (FR-23, FR-25). Thuộc PH01."""
import time

from database.security import verify_password
from protocol.constants import KHACH
from server.core import ANY, PUBLIC, ServerError, handler
from server.services import need, to_int


@handler("LOGIN", "PH01", PUBLIC)
def login(ctx, s, p):
    need(p, "username", "password")
    if s.channel != "lan":
        raise ServerError("FORBIDDEN", "Nhân viên chỉ đăng nhập qua mạng LAN")
    u = ctx.db.one("SELECT * FROM staff WHERE username=?", (p["username"],))
    if not u or not verify_password(p["password"], u["password_hash"]):
        raise ServerError("BAD_LOGIN", "Sai tên đăng nhập hoặc mật khẩu")
    if u["locked"]:
        raise ServerError("LOCKED", "Tài khoản đã bị khóa")
    s.role, s.user_id, s.name = u["role"], u["id"], u["full_name"]
    return {"role": s.role, "name": s.name, "user_id": s.user_id}


@handler("GUEST_CONNECT", "PH03", PUBLIC)
def guest_connect(ctx, s, p):
    """Khách order tại quán qua LAN: chỉ cần chọn bàn, không cần tài khoản."""
    if s.channel != "lan":
        raise ServerError("FORBIDDEN", "Chỉ dùng trong quán (LAN)")
    tid = to_int(p.get("table_id"), "Số bàn", 1)
    if not ctx.db.one("SELECT 1 FROM tables_cafe WHERE id=?", (tid,)):
        raise ServerError("NOT_FOUND", "Bàn không tồn tại")
    s.role, s.table_id, s.name = KHACH, tid, f"Khách bàn {tid}"
    return {"role": KHACH, "name": s.name, "table_id": tid}


@handler("TABLE_LIST", "PH03", PUBLIC)
def table_list(ctx, s, p):
    return {"rows": ctx.db.query("SELECT id, name FROM tables_cafe ORDER BY id")}


@handler("SYNC_REQUEST", "PH01", ANY)
def sync_request(ctx, s, p):
    """Client nối lại: xác nhận phiên còn hiệu lực. Dữ liệu nằm trong DB nên client chỉ cần tải lại."""
    return {"role": s.role, "name": s.name, "server_time": time.time()}
