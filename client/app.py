"""Ứng dụng client Tkinter: đăng nhập -> màn hình phân hệ -> menu chức năng -> giao diện thao tác."""
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

from client.modules import modules_for
from client.net import Connection
from client.ui_kit import ACCENT, BG, DARK, FG, ask_dialog

ROLE_TITLE = {"ADMIN": "Quản trị hệ thống", "QUANLY": "Quản lý", "CHUQUAN": "Chủ quán", "THUNGAN": "Thu ngân",
              "PHUCVU": "Nhân viên phục vụ", "PHACHE": "Nhân viên pha chế", "KHACH_BAN": "Khách tại quán",
              "KHACH_TK": "Khách đặt bàn từ xa"}

PUSH_TEXT = {
    "ORDER_READY": lambda p: f"Món của {p['table']} đã sẵn sàng (đơn #{p['order_id']})",
    "STAFF_CALLED": lambda p: f"{p['table']} gọi nhân viên",
    "SERVICE_REQUEST_NEW": lambda p: f"{p['table']} gửi yêu cầu chọn món (đơn #{p['order_id']})",
    "KITCHEN_NEW_ORDER": lambda p: f"Có đơn mới từ phục vụ: {p['table']} (đơn #{p['order_id']})",
    "ALERT_LATE_ORDER": lambda p: f"ĐƠN TRỄ: {p['table']}, chờ {p['wait_min']} phút ({p['items']})",
    "PAYMENT_REQUESTED": lambda p: f"{p['table']} yêu cầu thanh toán (đơn #{p['order_id']})",
    "PAYMENT_DONE": lambda p: f"Đã thanh toán đơn #{p['order_id']} ({p['table']})",
    "RESERVATION_NEW": lambda p: f"Đặt bàn mới/cập nhật từ {p['name']} (mã {p['id']})",
    "RESERVATION_UPDATED": lambda p: f"Đặt bàn #{p['id']} của bạn: {p['status']}",
    "MENU_UPDATED": lambda p: "Thực đơn vừa được cập nhật",
}
TOAST_TYPES = set(PUSH_TEXT) - {"MENU_UPDATED"}
KEEP_LOG = {"ORDER_READY", "STAFF_CALLED", "ALERT_LATE_ORDER"}


class App:
    def __init__(self, root, config):
        self.root, self.config = root, config
        root.title("Thức Coffee")
        root.geometry("1120x700")
        root.minsize(980, 620)
        root.configure(bg=BG)
        self._style()
        self.conn = None
        self.role = None          # vai trò thật từ server
        self.role_key = None      # khóa dùng cho menu (KHACH_BAN / KHACH_TK)
        self.name = ""
        self.readonly = False
        self.notifications = []
        self.relogin = None
        self.panel = None
        self.reconnecting = False
        self.frame = None
        self.toast_var = tk.StringVar()
        self.toast = tk.Label(root, textvariable=self.toast_var, bg=DARK, fg="#fff", anchor="w", padx=12, pady=6,
                              font=("Segoe UI", 10, "bold"))
        self._toast_job = None
        self.show_login()
        self.pump()

    def _style(self):
        st = ttk.Style()
        try:
            st.theme_use("clam")
        except tk.TclError:
            pass
        st.configure(".", background=BG, foreground=FG, font=("Segoe UI", 10))
        st.configure("TFrame", background=BG)
        st.configure("TLabel", background=BG, foreground=FG)
        st.configure("TButton", padding=6)
        st.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        st.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        st.configure("Title.TLabel", font=("Segoe UI", 20, "bold"))

    # ------------------------------------------------------------ mạng
    def call(self, msg_type, payload, cb=None):
        if self.conn is None or not self.conn.connected:
            if cb:
                cb({"type": "ERROR", "payload": {"code": "OFFLINE", "message": "Chưa kết nối tới server"}})
            return
        self.conn.send(msg_type, payload, cb)

    def pump(self):
        try:
            while self.conn is not None:
                try:
                    kind, msg = self.conn.inbox.get_nowait()
                except Exception:  # noqa: BLE001 (queue.Empty)
                    break
                if kind == "resp":
                    cb = self.conn.take_callback(msg.get("id"))
                    if cb:
                        cb(msg)
                elif kind == "push":
                    self.on_push(msg["type"], msg["payload"])
                elif kind == "closed":
                    self.on_closed()
        finally:
            self.root.after(50, self.pump)

    def on_push(self, t, p):
        if t == "FORCE_LOGOUT":
            messagebox.showwarning("Đã bị đăng xuất", p.get("reason", ""))
            self.logout()
            return
        if t in PUSH_TEXT:
            text = f"[{time.strftime('%H:%M:%S')}] {PUSH_TEXT[t](p)}"
            if t in KEEP_LOG:
                self.notifications.append((t, text))
            if t in TOAST_TYPES:
                self.show_toast(text, bad=(t == "ALERT_LATE_ORDER"))
        if self.panel is not None and self.panel.winfo_exists():
            self.panel.on_push(t, p)

    def show_toast(self, text, bad=False):
        self.toast.configure(bg="#b00020" if bad else DARK)
        self.toast_var.set(text)
        self.toast.pack(side="bottom", fill="x")
        self.root.bell()
        if self._toast_job:
            self.root.after_cancel(self._toast_job)
        self._toast_job = self.root.after(7000, self.toast.pack_forget)

    def on_closed(self):
        if self.relogin is None or self.reconnecting:
            return
        self.reconnecting = True
        self.show_toast("Mất kết nối tới server, đang thử kết nối lại...", bad=True)
        threading.Thread(target=self._reconnect, daemon=True).start()

    def _reconnect(self):
        host, port, use_ssl = self.conn_args
        while self.relogin is not None:
            time.sleep(3)
            try:
                c = Connection(host, port, use_ssl)
                c.connect()
            except OSError:
                continue
            self.root.after(0, lambda c=c: self._resume(c))
            return
        self.reconnecting = False

    def _resume(self, c):
        self.conn = c
        t, p = self.relogin

        def after_login(msg):
            self.reconnecting = False
            if msg["type"] == "ACK":
                self.call("SYNC_REQUEST", {}, lambda m: None)
                self.show_toast("Đã kết nối lại, dữ liệu được đồng bộ.")
                if self.panel is not None and self.panel.winfo_exists():
                    self.panel.refresh()
            else:
                self.logout()
        c.send(t, p, after_login)

    def connect(self, host, port, use_ssl):
        if self.conn:
            self.conn.close()
        c = Connection(host, port, use_ssl)
        c.connect()
        self.conn, self.conn_args = c, (host, port, use_ssl)

    # ------------------------------------------------------------ màn hình
    def set_frame(self, f):
        if self.frame is not None:
            self.frame.destroy()
        self.frame = f
        self.panel = None
        f.pack(fill="both", expand=True)
        self.toast.pack_forget()

    def logout(self):
        self.relogin = None
        self.role = self.role_key = None
        self.notifications.clear()
        if self.conn:
            self.conn.close()
        self.conn = None
        self.show_login()

    def show_login(self):
        f = ttk.Frame(self.root, padding=30)
        self.set_frame(f)
        ttk.Label(f, text="Thức Coffee", style="Title.TLabel").pack(pady=(10, 2))
        ttk.Label(f, text="Hệ thống quản lý quán cà phê", foreground=ACCENT).pack(pady=(0, 14))
        srv = ttk.Frame(f)
        srv.pack(pady=4)
        ttk.Label(srv, text="Địa chỉ server").grid(row=0, column=0, padx=6)
        self.host_var = tk.StringVar(value=self.config.get("server_address", "127.0.0.1"))
        ttk.Entry(srv, textvariable=self.host_var, width=22).grid(row=0, column=1)
        nb = ttk.Notebook(f)
        nb.pack(pady=14)
        # --- nhân viên
        t1 = ttk.Frame(nb, padding=20)
        nb.add(t1, text="Nhân viên / Quản lý / Chủ quán / Admin")
        self.u_var, self.p_var = tk.StringVar(), tk.StringVar()
        for i, (txt, var, show) in enumerate((("Tên đăng nhập", self.u_var, ""), ("Mật khẩu", self.p_var, "*"))):
            ttk.Label(t1, text=txt).grid(row=i, column=0, sticky="w", pady=6, padx=(0, 12))
            e = ttk.Entry(t1, textvariable=var, width=30, show=show)
            e.grid(row=i, column=1)
            e.bind("<Return>", lambda ev: self.login_staff())
        ttk.Button(t1, text="Đăng nhập", command=self.login_staff).grid(row=2, column=1, sticky="e", pady=10)
        # --- khách tại quán
        t2 = ttk.Frame(nb, padding=20)
        nb.add(t2, text="Khách tại quán")
        ttk.Label(t2, text="Chọn số bàn của bạn", wraplength=300).grid(row=0, column=0, columnspan=2, pady=6)
        self.table_var = tk.IntVar(value=1)
        ttk.Spinbox(t2, from_=1, to=99, textvariable=self.table_var, width=6).grid(row=1, column=0, pady=6)
        ttk.Button(t2, text="Vào gọi món", command=self.login_guest).grid(row=1, column=1, padx=12)
        # --- khách đặt bàn
        t3 = ttk.Frame(nb, padding=20)
        nb.add(t3, text="Khách đặt bàn từ xa")
        self.ph_var, self.cp_var = tk.StringVar(), tk.StringVar()
        for i, (txt, var, show) in enumerate((("Số điện thoại", self.ph_var, ""), ("Mật khẩu", self.cp_var, "*"))):
            ttk.Label(t3, text=txt).grid(row=i, column=0, sticky="w", pady=6, padx=(0, 12))
            ttk.Entry(t3, textvariable=var, width=30, show=show).grid(row=i, column=1)
        bar = ttk.Frame(t3)
        bar.grid(row=2, column=1, sticky="e", pady=10)
        ttk.Button(bar, text="Đăng ký", command=self.register).pack(side="left", padx=4)
        ttk.Button(bar, text="Đăng nhập", command=self.login_customer).pack(side="left")
        self.login_msg = tk.StringVar()
        ttk.Label(f, textvariable=self.login_msg, foreground="#b00020", wraplength=520).pack()

    def _login(self, port, use_ssl, msg_type, payload, role_key=None):
        try:
            self.connect(self.host_var.get().strip(), port, use_ssl)
        except OSError as e:
            self.login_msg.set(f"Không kết nối được tới server: {e}")
            return
        self.login_msg.set("Đang đăng nhập...")

        def done(msg):
            if msg["type"] != "ACK":
                self.login_msg.set(msg["payload"].get("message", "Đăng nhập thất bại"))
                return
            pl = msg["payload"]
            self.role = pl["role"]
            self.name = pl.get("name", "")
            self.table_id = pl.get("table_id")
            self.role_key = role_key or self.role
            self.relogin = (msg_type, payload)
            self.show_home()
        self.conn.send(msg_type, payload, done)

    def login_staff(self):
        self._login(self.config["port_lan"], False, "LOGIN", {"username": self.u_var.get().strip(), "password": self.p_var.get()})

    def login_guest(self):
        self._login(self.config["port_lan"], False, "GUEST_CONNECT", {"table_id": self.table_var.get()}, "KHACH_BAN")

    def login_customer(self):
        self._login(self.config["port_internet"], bool(self.config.get("internet_ssl")), "CUSTOMER_LOGIN",
                    {"phone": self.ph_var.get().strip(), "password": self.cp_var.get()}, "KHACH_TK")

    def register(self):
        data = ask_dialog(self.root, "Đăng ký tài khoản khách", [("full_name", "Họ tên", "text"),
                          ("phone", "Số điện thoại", "text"), ("password", "Mật khẩu (>= 6 ký tự)", "password")])
        if not data:
            return
        try:
            self.connect(self.host_var.get().strip(), self.config["port_internet"], bool(self.config.get("internet_ssl")))
        except OSError as e:
            self.login_msg.set(f"Không kết nối được tới server: {e}")
            return

        def done(msg):
            if msg["type"] == "ACK":
                self.ph_var.set(data["phone"])
                self.login_msg.set("")
                messagebox.showinfo("Đăng ký", "Đăng ký thành công. Hãy nhập mật khẩu và đăng nhập.")
            else:
                self.login_msg.set(msg["payload"].get("message", "Đăng ký thất bại"))
        self.conn.send("CUSTOMER_REGISTER", data, done)

    # ------------------------------------------------------------ màn hình chính (các phân hệ)
    def show_home(self):
        f = ttk.Frame(self.root, padding=24)
        self.set_frame(f)
        top = ttk.Frame(f)
        top.pack(fill="x")
        ttk.Label(top, text=f"{self.name}  ·  {ROLE_TITLE.get(self.role_key, self.role_key)}", style="Title.TLabel").pack(side="left")
        ttk.Button(top, text="Đăng xuất", command=self.logout).pack(side="right")
        mods = modules_for(self.role_key)
        sub = "Admin thấy tất cả phân hệ kèm trạng thái hoạt động." if self.role_key == "ADMIN" else "Chọn một phân hệ để bắt đầu."
        ttk.Label(f, text=sub, foreground=ACCENT).pack(anchor="w", pady=(6, 16))
        grid = ttk.Frame(f)
        grid.pack(anchor="nw")
        self.cards = {}
        for i, (code, name, funcs) in enumerate(mods):
            card = tk.Frame(grid, bg="#fff", highlightbackground="#dccfbf", highlightthickness=1, width=230, height=110, cursor="hand2")
            card.grid(row=i // 4, column=i % 4, padx=8, pady=8)
            card.pack_propagate(False)
            tk.Label(card, text=code, bg="#fff", fg=ACCENT, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=12, pady=(10, 0))
            tk.Label(card, text=name, bg="#fff", fg=FG, font=("Segoe UI", 12, "bold"), wraplength=200, justify="left").pack(anchor="w", padx=12)
            st = tk.Label(card, text="", bg="#fff", fg="#6b5a4c", font=("Segoe UI", 9))
            st.pack(anchor="w", padx=12, pady=(4, 0))
            self.cards[code] = st
            for w in [card] + card.winfo_children():
                w.bind("<Button-1>", lambda e, c=code, n=name, fl=funcs: self.open_module(c, n, fl))
        if self.role_key == "ADMIN":
            self._poll_status()

    def _poll_status(self):
        if self.frame is None or not self.frame.winfo_exists() or not getattr(self, "cards", None):
            return
        if not any(w.winfo_exists() for w in self.cards.values()):
            return

        def done(msg):
            if msg["type"] != "ACK":
                return
            for r in msg["payload"]["rows"]:
                w = self.cards.get(r["code"])
                if w is not None and w.winfo_exists():
                    color = {"Hoạt động": "#1b7f3b", "Lỗi": "#b00020"}.get(r["status"], "#6b5a4c")
                    w.configure(text=f"● {r['status']} · {r['clients']} client", fg=color)
        self.call("ADMIN_STATUS", {}, done)
        self.root.after(5000, self._poll_status)

    # ------------------------------------------------------------ vào một phân hệ
    def open_module(self, code, name, funcs):
        self.readonly = (self.role_key == "ADMIN" and code != "PH01")
        f = ttk.Frame(self.root, padding=14)
        self.set_frame(f)
        top = ttk.Frame(f)
        top.pack(fill="x", pady=(0, 8))
        ttk.Button(top, text="← Màn hình chính", command=self.show_home).pack(side="left")
        ttk.Label(top, text=f"  {code} · {name}", style="Title.TLabel").pack(side="left")
        if self.readonly:
            ttk.Label(top, text="   Chế độ giám sát (chỉ xem)", foreground="#b00020").pack(side="left")
        body = ttk.PanedWindow(f, orient="horizontal")
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body)
        right = ttk.Frame(body, padding=(14, 0, 0, 0))
        body.add(left, weight=0)
        body.add(right, weight=1)
        tree = ttk.Treeview(left, show="tree", selectmode="browse", height=24)
        tree.column("#0", width=300)
        tree.pack(fill="y", expand=True)
        factories, first = {}, None
        for fn, cons in funcs:
            pid = tree.insert("", "end", text=fn, open=True)
            for label, factory in cons:
                iid = tree.insert(pid, "end", text="   " + label)
                factories[iid] = (label, factory)
                first = first or iid

        def show(_=None):
            sel = tree.selection()
            if not sel or sel[0] not in factories:
                return
            label, factory = factories[sel[0]]
            for w in right.winfo_children():
                w.destroy()
            ttk.Label(right, text=label, font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 8))
            self.panel = factory(right, self)
            self.panel.pack(fill="both", expand=True)
        tree.bind("<<TreeviewSelect>>", show)
        if first:
            tree.selection_set(first)


def run(config):
    root = tk.Tk()
    App(root, config)
    root.mainloop()
