"""Màn hình gọi món của khách tại bàn (PH03): chọn món, số lượng, ghi chú, gửi yêu cầu cho phục vụ."""
import tkinter as tk
from tkinter import messagebox, ttk

from client.ui_kit import ACCENT, Panel, money

# ── Color palette ──────────────────────────────────────────────────
_BG        = "#FAF6F1"
_CARD_BG   = "#FFFFFF"
_BORDER    = "#E8DDD3"
_ACCENT    = "#C67C4E"
_ACCENT_LT = "#FFF3E9"
_SUCCESS   = "#2D8B4E"
_ERROR     = "#D32F2F"
_TEXT      = "#3C2415"
_TEXT_SEC  = "#7A6555"
_ROW_ALT   = "#FDF8F3"

_FONT      = "Segoe UI"
_FONT_SM   = (_FONT, 10)
_FONT_MD   = (_FONT, 11)
_FONT_LG   = (_FONT, 13, "bold")
_FONT_XL   = (_FONT, 15, "bold")
_FONT_HDR  = (_FONT, 14, "bold")


def _style_once():
    """Register custom ttk styles (idempotent)."""
    s = ttk.Style()
    if "OrderPanel._done" in s.element_names():
        return

    # ── Treeview ───────────────────────────────────────────────
    s.configure(
        "Order.Treeview",
        background=_CARD_BG,
        fieldbackground=_CARD_BG,
        foreground=_TEXT,
        font=_FONT_MD,
        rowheight=30,
        borderwidth=0,
    )
    s.configure(
        "Order.Treeview.Heading",
        background=_ACCENT_LT,
        foreground=_ACCENT,
        font=(_FONT, 10, "bold"),
        borderwidth=0,
        relief="flat",
        padding=(8, 6),
    )
    s.map(
        "Order.Treeview.Heading",
        background=[("active", _ACCENT_LT)],
    )
    s.map(
        "Order.Treeview",
        background=[("selected", _ACCENT_LT)],
        foreground=[("selected", _ACCENT)],
    )

    # ── Accent button ─────────────────────────────────────────
    s.configure(
        "Accent.TButton",
        background=_ACCENT,
        foreground="#FFFFFF",
        font=(_FONT, 11, "bold"),
        padding=(18, 8),
        borderwidth=0,
        relief="flat",
    )
    s.map(
        "Accent.TButton",
        background=[("active", "#A0623B"), ("disabled", _BORDER)],
        foreground=[("disabled", _TEXT_SEC)],
    )

    # ── Large send button ─────────────────────────────────────
    s.configure(
        "Send.TButton",
        background=_ACCENT,
        foreground="#FFFFFF",
        font=(_FONT, 12, "bold"),
        padding=(22, 10),
        borderwidth=0,
        relief="flat",
    )
    s.map(
        "Send.TButton",
        background=[("active", "#A0623B"), ("disabled", _BORDER)],
        foreground=[("disabled", _TEXT_SEC)],
    )

    # ── Subtle / gray button ──────────────────────────────────
    s.configure(
        "Subtle.TButton",
        background="#EDE6DD",
        foreground=_TEXT_SEC,
        font=_FONT_MD,
        padding=(14, 7),
        borderwidth=0,
        relief="flat",
    )
    s.map(
        "Subtle.TButton",
        background=[("active", _BORDER)],
    )

    # ── Spinbox ───────────────────────────────────────────────
    s.configure(
        "Order.TSpinbox",
        arrowsize=14,
        padding=(6, 4),
        font=_FONT_MD,
    )

    # Mark as initialised via a no-op element
    try:
        s.element_create("OrderPanel._done", "from", "default")
    except tk.TclError:
        pass


def _card(parent, **kw):
    """Return a tk.Frame styled as a white card with subtle border."""
    f = tk.Frame(
        parent,
        bg=_CARD_BG,
        highlightbackground=_BORDER,
        highlightthickness=1,
        bd=0,
        **kw,
    )
    return f


def _alternating_rows(tree):
    """Apply alternating row colours to a Treeview."""
    tree.tag_configure("odd", background=_CARD_BG)
    tree.tag_configure("even", background=_ROW_ALT)
    for idx, iid in enumerate(tree.get_children()):
        tree.item(iid, tags=("even",) if idx % 2 else ("odd",))


class OrderPanel(Panel):
    refresh_on = ("MENU_UPDATED",)

    # ──────────────────────────────────────────────────────────
    #  Construction
    # ──────────────────────────────────────────────────────────
    def __init__(self, parent, app):
        super().__init__(parent, app)
        _style_once()

        self.menu, self.cart = [], []

        # Root canvas background
        self.configure(style="TFrame")
        root_bg = tk.Frame(self, bg=_BG)
        root_bg.pack(fill="both", expand=True)

        # ── Outer horizontal container ────────────────────────
        outer = tk.Frame(root_bg, bg=_BG)
        outer.pack(fill="both", expand=True, padx=16, pady=14)

        # ── LEFT panel ────────────────────────────────────────
        left = tk.Frame(outer, bg=_BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))

        # Header
        hdr_left = tk.Frame(left, bg=_BG)
        hdr_left.pack(fill="x", pady=(0, 8))
        tk.Label(
            hdr_left, text="📋  Thực đơn", font=_FONT_HDR,
            fg=_ACCENT, bg=_BG, anchor="w",
        ).pack(side="left")

        # Menu card
        menu_card = _card(left)
        menu_card.pack(fill="both", expand=True)

        menu_inner = tk.Frame(menu_card, bg=_CARD_BG)
        menu_inner.pack(fill="both", expand=True, padx=2, pady=2)

        self.mt = ttk.Treeview(
            menu_inner,
            columns=("name", "price", "state"),
            show="headings",
            height=14,
            selectmode="browse",
            style="Order.Treeview",
        )
        for col_id, heading, w, anc in (
            ("name", "Món", 220, "w"),
            ("price", "Giá (đ)", 100, "e"),
            ("state", "Tình trạng", 100, "center"),
        ):
            self.mt.heading(col_id, text=heading)
            self.mt.column(col_id, width=w, anchor=anc, stretch=True)

        menu_sb = ttk.Scrollbar(menu_inner, orient="vertical", command=self.mt.yview)
        self.mt.configure(yscrollcommand=menu_sb.set)
        self.mt.pack(side="left", fill="both", expand=True)
        menu_sb.pack(side="right", fill="y")

        # ── Control bar (below menu, inside left column) ──────
        ctrl_card = _card(left)
        ctrl_card.pack(fill="x", pady=(10, 0))

        row = tk.Frame(ctrl_card, bg=_CARD_BG)
        row.pack(fill="x", padx=14, pady=12)

        tk.Label(row, text="Số lượng", font=_FONT_MD, fg=_TEXT, bg=_CARD_BG).pack(side="left")
        self.qty = tk.IntVar(value=1)
        ttk.Spinbox(
            row, from_=1, to=50, textvariable=self.qty,
            width=5, style="Order.TSpinbox",
        ).pack(side="left", padx=(6, 16))

        tk.Label(row, text="Ghi chú", font=_FONT_MD, fg=_TEXT, bg=_CARD_BG).pack(side="left")
        self.note = tk.StringVar()
        note_entry = ttk.Entry(row, textvariable=self.note, width=26, font=_FONT_MD)
        note_entry.pack(side="left", padx=(6, 16))

        self.add_btn = ttk.Button(
            row, text="  Thêm vào giỏ  ➕", style="Accent.TButton",
            command=self.add,
        )
        self.add_btn.pack(side="left")

        # ── Vertical divider ──────────────────────────────────
        divider = tk.Frame(outer, bg=_BORDER, width=2)
        divider.pack(side="left", fill="y", padx=8)

        # ── RIGHT panel ───────────────────────────────────────
        right = tk.Frame(outer, bg=_BG)
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))

        # Header
        hdr_right = tk.Frame(right, bg=_BG)
        hdr_right.pack(fill="x", pady=(0, 8))
        tk.Label(
            hdr_right, text="🛒  Giỏ của bạn", font=_FONT_HDR,
            fg=_ACCENT, bg=_BG, anchor="w",
        ).pack(side="left")

        # Cart card
        cart_card = _card(right)
        cart_card.pack(fill="both", expand=True)

        cart_inner = tk.Frame(cart_card, bg=_CARD_BG)
        cart_inner.pack(fill="both", expand=True, padx=2, pady=2)

        self.ct = ttk.Treeview(
            cart_inner,
            columns=("name", "qty", "note", "sub"),
            show="headings",
            height=14,
            selectmode="browse",
            style="Order.Treeview",
        )
        for col_id, heading, w, anc in (
            ("name", "Món", 170, "w"),
            ("qty", "SL", 50, "center"),
            ("note", "Ghi chú", 130, "w"),
            ("sub", "Thành tiền", 110, "e"),
        ):
            self.ct.heading(col_id, text=heading)
            self.ct.column(col_id, width=w, anchor=anc, stretch=True)

        cart_sb = ttk.Scrollbar(cart_inner, orient="vertical", command=self.ct.yview)
        self.ct.configure(yscrollcommand=cart_sb.set)
        self.ct.pack(side="left", fill="both", expand=True)
        cart_sb.pack(side="right", fill="y")

        # ── Total bar ─────────────────────────────────────────
        total_bar = tk.Frame(right, bg=_ACCENT_LT, bd=0,
                             highlightbackground=_BORDER, highlightthickness=1)
        total_bar.pack(fill="x", pady=(10, 0), ipady=6)

        self.total = tk.StringVar(value="☕  Tổng: 0 đ")
        tk.Label(
            total_bar, textvariable=self.total, font=_FONT_XL,
            fg=_ACCENT, bg=_ACCENT_LT, anchor="w",
        ).pack(side="left", padx=14)

        # ── Action buttons ────────────────────────────────────
        btn_bar = tk.Frame(right, bg=_BG)
        btn_bar.pack(fill="x", pady=(12, 0))

        ttk.Button(
            btn_bar, text="🗑  Xóa dòng", style="Subtle.TButton",
            command=self.remove,
        ).pack(side="left")

        self.send_btn = ttk.Button(
            btn_bar, text="  ✅  Gửi yêu cầu cho phục vụ  ", style="Send.TButton",
            command=self.send,
        )
        self.send_btn.pack(side="right")

        # ── Message area ──────────────────────────────────────
        self.msg = tk.StringVar()
        self._msg_label = tk.Label(
            right, textvariable=self.msg, font=(_FONT, 11),
            fg=_ACCENT, bg=_BG, anchor="w", wraplength=420, justify="left",
        )
        self._msg_label.pack(fill="x", anchor="w", pady=(8, 0))

        # ── Read-only guard ───────────────────────────────────
        if app.readonly:
            self.add_btn.state(["disabled"])
            self.send_btn.state(["disabled"])
            self.msg.set("Chế độ giám sát: chỉ xem giao diện, không thực hiện thao tác nghiệp vụ.")
        else:
            self.refresh()

    # ──────────────────────────────────────────────────────────
    #  Data fetching
    # ──────────────────────────────────────────────────────────
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
        _alternating_rows(self.mt)

    # ──────────────────────────────────────────────────────────
    #  Cart actions
    # ──────────────────────────────────────────────────────────
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
        self.total.set(f"☕  Tổng: {money(total)} đ")
        _alternating_rows(self.ct)

    def send(self):
        if not self.cart:
            messagebox.showinfo("Giỏ trống", "Chưa có món nào trong giỏ.")
            return
        items = [{"menu_item_id": c["menu_item_id"], "quantity": c["quantity"], "note": c["note"]} for c in self.cart]

        def done(msg):
            if not self.winfo_exists():
                return
            if msg["type"] == "ACK":
                self.msg.set(f"✓  Đã gửi yêu cầu (đơn #{msg['payload']['order_id']}). Nhân viên phục vụ sẽ xử lý.")
                self._msg_label.configure(fg=_SUCCESS)
                self.cart.clear()
                self.redraw()
            else:
                self.msg.set("✗  Lỗi: " + msg["payload"].get("message", ""))
                self._msg_label.configure(fg=_ERROR)
        self.app.call("ORDER_REQUEST", {"items": items}, done)
