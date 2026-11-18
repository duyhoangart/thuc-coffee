"""Màn hình gọi món của khách tại bàn (PH03): chọn món, số lượng, ghi chú, gửi yêu cầu cho phục vụ."""
import tkinter as tk
from tkinter import messagebox, ttk

from client.ui_kit import ACCENT, Panel, money


class OrderPanel(Panel):
    refresh_on = ("MENU_UPDATED",)

    def __init__(self, parent, app):
        super().__init__(parent, app)
        self.menu, self.cart = [], []
        left = ttk.Frame(self)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(left, text="Thực đơn", foreground=ACCENT).pack(anchor="w")
        self.mt = ttk.Treeview(left, columns=("name", "price", "state"), show="headings", height=12, selectmode="browse")
        for k, t, w in (("name", "Món", 190), ("price", "Giá (đ)", 80), ("state", "Tình trạng", 80)):
            self.mt.heading(k, text=t)
            self.mt.column(k, width=w)
        self.mt.pack(fill="both", expand=True)
        row = ttk.Frame(left)
        row.pack(fill="x", pady=6)
        ttk.Label(row, text="Số lượng").pack(side="left")
        self.qty = tk.IntVar(value=1)
        ttk.Spinbox(row, from_=1, to=50, textvariable=self.qty, width=5).pack(side="left", padx=6)
        ttk.Label(row, text="Ghi chú").pack(side="left")
        self.note = tk.StringVar()
        ttk.Entry(row, textvariable=self.note, width=22).pack(side="left", padx=6)
        self.add_btn = ttk.Button(row, text="Thêm vào giỏ", command=self.add)
        self.add_btn.pack(side="left")
        ttk.Label(right, text="Giỏ của bàn bạn", foreground=ACCENT).pack(anchor="w")
        self.ct = ttk.Treeview(right, columns=("name", "qty", "note", "sub"), show="headings", height=12, selectmode="browse")
        for k, t, w in (("name", "Món", 150), ("qty", "SL", 40), ("note", "Ghi chú", 110), ("sub", "Thành tiền", 90)):
            self.ct.heading(k, text=t)
            self.ct.column(k, width=w)
        self.ct.pack(fill="both", expand=True)
        self.total = tk.StringVar(value="Tổng: 0 đ")
        ttk.Label(right, textvariable=self.total, font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=4)
        bar = ttk.Frame(right)
        bar.pack(fill="x")
        ttk.Button(bar, text="Xóa dòng", command=self.remove).pack(side="left")
        self.send_btn = ttk.Button(bar, text="Gửi yêu cầu cho phục vụ", command=self.send)
        self.send_btn.pack(side="right")
        self.msg = tk.StringVar()
        ttk.Label(right, textvariable=self.msg, foreground=ACCENT, wraplength=380).pack(anchor="w", pady=4)
        if app.readonly:
            self.add_btn.state(["disabled"])
            self.send_btn.state(["disabled"])
            self.msg.set("Chế độ giám sát: chỉ xem giao diện, không thực hiện thao tác nghiệp vụ.")
        else:
            self.refresh()

    def refresh(self):
        if self.app.readonly or not self.winfo_exists():
            return
        self.app.call("MENU_LIST", {}, self._fill_menu)

    def _fill_menu(self, msg):
        if msg["type"] != "ACK" or not self.winfo_exists():
            return
        self.menu = msg["payload"]["rows"]
        self.mt.delete(*self.mt.get_children())
        for r in self.menu:
            self.mt.insert("", "end", values=(r["name"], money(r["price"]), r["state"]))

    def add(self):
        sel = self.mt.selection()
        if not sel:
            messagebox.showinfo("Chưa chọn", "Hãy chọn một món trong thực đơn.")
            return
        m = self.menu[self.mt.index(sel[0])]
        if not m["available"]:
            messagebox.showwarning("Hết hàng", f"{m['name']} đã hết hàng.")
            return
        try:
            q = int(self.qty.get())
        except (tk.TclError, ValueError):
            q = 0
        if not 1 <= q <= 50:
            messagebox.showwarning("Số lượng", "Số lượng phải từ 1 đến 50.")
            return
        self.cart.append({"menu_item_id": m["id"], "name": m["name"], "price": m["price"], "quantity": q,
                          "note": self.note.get().strip()})
        self.note.set("")
        self.redraw()

    def remove(self):
        sel = self.ct.selection()
        if sel:
            del self.cart[self.ct.index(sel[0])]
            self.redraw()

    def redraw(self):
        self.ct.delete(*self.ct.get_children())
        total = 0
        for c in self.cart:
            sub = c["price"] * c["quantity"]
            total += sub
            self.ct.insert("", "end", values=(c["name"], c["quantity"], c["note"], money(sub)))
        self.total.set(f"Tổng: {money(total)} đ")

    def send(self):
        if not self.cart:
            messagebox.showinfo("Giỏ trống", "Chưa có món nào trong giỏ.")
            return
        items = [{"menu_item_id": c["menu_item_id"], "quantity": c["quantity"], "note": c["note"]} for c in self.cart]

        def done(msg):
            if not self.winfo_exists():
                return
            if msg["type"] == "ACK":
                self.msg.set(f"Đã gửi yêu cầu (đơn #{msg['payload']['order_id']}). Nhân viên phục vụ sẽ xử lý.")
                self.cart.clear()
                self.redraw()
            else:
                self.msg.set("Lỗi: " + msg["payload"].get("message", ""))
        self.app.call("ORDER_REQUEST", {"items": items}, done)
