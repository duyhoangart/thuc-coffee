import os
import sqlite3
import threading
import time

from database.security import hash_password

SCHEMA = os.path.join(os.path.dirname(__file__), "schema.sql")

DEFAULT_SETTINGS = {"late_threshold_minutes": "10", "heartbeat_interval_sec": "5", "heartbeat_timeout_sec": "15"}

# Tài khoản mẫu CHỈ để chạy thử. Đổi mật khẩu khi dùng thật.
DEMO_STAFF = [
    ("admin", "admin123", "Quản trị hệ thống", "ADMIN"),
    ("chuquan", "chuquan123", "Chủ quán", "CHUQUAN"),
    ("quanly", "quanly123", "Quản lý ca", "QUANLY"),
    ("thungan", "thungan123", "Thu ngân", "THUNGAN"),
    ("phucvu", "phucvu123", "Phục vụ 1", "PHUCVU"),
    ("phache", "phache123", "Pha chế 1", "PHACHE"),
]
DEMO_MENU = [
    ("Cà phê đen", "Cà phê phin truyền thống", 25000, "Cà phê"),
    ("Cà phê sữa", "Cà phê phin với sữa đặc", 29000, "Cà phê"),
    ("Bạc xỉu", "Nhiều sữa, ít cà phê", 32000, "Cà phê"),
    ("Trà đào", "Trà đào cam sả", 39000, "Trà"),
    ("Trà vải", "Trà vải thanh mát", 39000, "Trà"),
    ("Sinh tố bơ", "Bơ sáp xay sữa", 45000, "Sinh tố"),
    ("Bánh tiramisu", "Bánh ngọt", 42000, "Bánh"),
    ("Nước suối", "Chai 500ml", 12000, "Khác"),
]
NUM_TABLES = 10


class Database:
    def __init__(self, path):
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        self.path = path
        self.lock = threading.RLock()
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        with open(SCHEMA, encoding="utf-8") as f:
            self.conn.executescript(f.read())
        self.conn.commit()
        self._seed()

    # ---- truy vấn ----
    def query(self, sql, args=()):
        with self.lock:
            return [dict(r) for r in self.conn.execute(sql, args).fetchall()]

    def one(self, sql, args=()):
        rows = self.query(sql, args)
        return rows[0] if rows else None

    def execute(self, sql, args=()):
        with self.lock:
            cur = self.conn.execute(sql, args)
            self.conn.commit()
            return cur.lastrowid

    # ---- cấu hình ----
    def get_setting(self, key):
        r = self.one("SELECT value FROM settings WHERE key=?", (key,))
        return r["value"] if r else DEFAULT_SETTINGS.get(key)

    def set_setting(self, key, value):
        self.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                     "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))

    # ---- sao lưu / phục hồi (dùng sqlite3 backup API, an toàn khi đang chạy) ----
    def backup_to(self, dest):
        with self.lock:
            out = sqlite3.connect(dest)
            try:
                self.conn.backup(out)
            finally:
                out.close()

    def restore_from(self, src):
        with self.lock:
            inp = sqlite3.connect(src)
            try:
                inp.backup(self.conn)
            finally:
                inp.close()

    def integrity_check(self):
        return self.query("PRAGMA integrity_check")[0]["integrity_check"]

    def _seed(self):
        now = time.time()
        if not self.one("SELECT 1 FROM staff LIMIT 1"):
            for u, p, n, r in DEMO_STAFF:
                self.execute("INSERT INTO staff(username,password_hash,full_name,role,created_at) VALUES(?,?,?,?,?)",
                             (u, hash_password(p), n, r, now))
        if not self.one("SELECT 1 FROM menu_items LIMIT 1"):
            for n, d, pr, c in DEMO_MENU:
                self.execute("INSERT INTO menu_items(name,description,price,category) VALUES(?,?,?,?)", (n, d, pr, c))
        if not self.one("SELECT 1 FROM tables_cafe LIMIT 1"):
            for i in range(1, NUM_TABLES + 1):
                self.execute("INSERT INTO tables_cafe(id,name) VALUES(?,?)", (i, f"Bàn {i}"))
