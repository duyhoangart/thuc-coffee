"""PH01 - Quản trị hệ thống (Admin): giám sát phân hệ, kết nối, cấu hình, dữ liệu, an ninh."""
import os
import time

from protocol.constants import ADMIN, MODULE_NAMES, MODULE_ROLES
from server.core import ServerError, handler
from server.services import fmt_dt, need

BACKUP_DIR = "data/backups"


@handler("ADMIN_STATUS", "PH01", [ADMIN])
def admin_status(ctx, s, p):
    sessions = ctx.online()
    rows = []
    for code, name in MODULE_NAMES.items():
        n = sum(1 for x in sessions if x.role in MODULE_ROLES[code])
        err = ctx.recent_errors(code)
        last = ctx.activity.get(code)
        status = "Lỗi" if err else ("Hoạt động" if code == "PH01" or n else "Chưa có client")
        rows.append({"code": code, "name": name, "clients": n, "last": fmt_dt(last), "errors": err, "status": status})
    return {"rows": rows, "uptime_min": int((time.time() - ctx.started_at) // 60)}


@handler("ADMIN_SESSIONS", "PH01", [ADMIN])
def admin_sessions(ctx, s, p):
    return {"rows": [{"id": x.id, "ip": x.ip, "channel": x.channel, "role": x.role or "-", "name": x.name,
                      "since": fmt_dt(x.connected_at), "idle": int(time.time() - x.last_seen)}
                     for x in list(ctx.sessions.values()) if x.alive]}


@handler("ADMIN_KICK", "PH01", [ADMIN])
def admin_kick(ctx, s, p):
    need(p, "session_id")
    t = ctx.sessions.get(int(p["session_id"]))
    if not t:
        raise ServerError("NOT_FOUND", "Session không còn tồn tại")
    if t.id == s.id:
        raise ServerError("BAD_REQUEST", "Không thể tự ngắt session của mình")
    t.close()
    return {}


@handler("ADMIN_CONFIG_GET", "PH01", [ADMIN])
def admin_config_get(ctx, s, p):
    c = ctx.config
    rows = [{"key": "Cổng LAN", "value": c["port_lan"]}, {"key": "Cổng Internet", "value": c["port_internet"]},
            {"key": "SSL/TLS cổng Internet", "value": "Bật" if ctx.config.get("_ssl_active") else "Tắt"},
            {"key": "Chu kỳ heartbeat (giây)", "value": ctx.db.get_setting("heartbeat_interval_sec")},
            {"key": "Hết hạn heartbeat (giây)", "value": ctx.db.get_setting("heartbeat_timeout_sec")}]
    return {"rows": rows}


@handler("ADMIN_CONFIG_SET", "PH01", [ADMIN])
def admin_config_set(ctx, s, p):
    need(p, "heartbeat_interval_sec", "heartbeat_timeout_sec")
    a, b = int(p["heartbeat_interval_sec"]), int(p["heartbeat_timeout_sec"])
    if a < 1 or b <= a:
        raise ServerError("BAD_REQUEST", "Hết hạn phải lớn hơn chu kỳ, chu kỳ >= 1")
    ctx.db.set_setting("heartbeat_interval_sec", a)
    ctx.db.set_setting("heartbeat_timeout_sec", b)
    return {}


@handler("ADMIN_DB_CHECK", "PH01", [ADMIN])
def admin_db_check(ctx, s, p):
    return {"result": ctx.db.integrity_check()}


@handler("ADMIN_BACKUP", "PH01", [ADMIN])
def admin_backup(ctx, s, p):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    name = time.strftime("backup_%Y%m%d_%H%M%S.db")
    ctx.db.backup_to(os.path.join(BACKUP_DIR, name))
    return {"name": name}


@handler("ADMIN_BACKUP_LIST", "PH01", [ADMIN])
def admin_backup_list(ctx, s, p):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    names = sorted((n for n in os.listdir(BACKUP_DIR) if n.endswith(".db")), reverse=True)
    return {"rows": [{"name": n, "size_kb": os.path.getsize(os.path.join(BACKUP_DIR, n)) // 1024} for n in names]}


@handler("ADMIN_RESTORE", "PH01", [ADMIN])
def admin_restore(ctx, s, p):
    need(p, "name")
    name = os.path.basename(p["name"])  # chặn đường dẫn lạ
    path = os.path.join(BACKUP_DIR, name)
    if not os.path.isfile(path):
        raise ServerError("NOT_FOUND", "Không tìm thấy bản sao lưu")
    ctx.db.restore_from(path)
    return {}


@handler("ADMIN_CUSTOMERS", "PH01", [ADMIN])
def admin_customers(ctx, s, p):
    rows = ctx.db.query("SELECT id, phone, full_name, locked FROM customers ORDER BY id DESC LIMIT 200")
    for r in rows:
        r["state"] = "Đang khóa" if r["locked"] else "Bình thường"
    return {"rows": rows}


@handler("ADMIN_LOCK_CUSTOMER", "PH01", [ADMIN])
def admin_lock_customer(ctx, s, p):
    need(p, "id")
    locked = 1 if p.get("locked", True) else 0
    ctx.db.execute("UPDATE customers SET locked=? WHERE id=?", (locked, int(p["id"])))
    if locked:
        for x in ctx.online(where=lambda x: x.customer_id == int(p["id"])):
            x.close()
    return {}


@handler("ADMIN_BLOCK_IP", "PH01", [ADMIN])
def admin_block_ip(ctx, s, p):
    need(p, "ip")
    if p.get("blocked", True):
        ctx.blocked_ips.add(p["ip"])
        for x in ctx.online(where=lambda x: x.ip == p["ip"]):
            x.close()
    else:
        ctx.blocked_ips.discard(p["ip"])
    return {}


@handler("ADMIN_REJECTED", "PH01", [ADMIN])
def admin_rejected(ctx, s, p):
    rows = [{"time": fmt_dt(r["time"]), "ip": r["ip"], "role": r["role"], "type": r["type"], "code": r["code"]}
            for r in reversed(list(ctx.rejected))]
    return {"rows": rows, "blocked_ips": sorted(ctx.blocked_ips)}
