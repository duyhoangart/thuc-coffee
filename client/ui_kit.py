"""Các panel dùng chung: danh sách + nút thao tác, biểu mẫu, hộp thoại nhập."""
import tkinter as tk
from tkinter import messagebox, ttk

BG, FG, ACCENT, DARK = "#FAF6F1", "#1A1A2E", "#C67C4E", "#1A1A2E"

# ── internal palette (not exported) ──────────────────────────────
_CARD      = "#FFFFFF"
_BORDER    = "#E8DDD3"
_SUCCESS   = "#2D8B4E"
_ERROR     = "#D32F2F"
_HOVER     = "#B5673E"
_INPUT_BG  = "#FFFFFF"
_SECONDARY = "#6B7280"
_LIGHT_ACC = "#FFF3E9"
_BTN_FG    = "#FFFFFF"
_GOLD      = "#D4A76A"
_SIDEBAR   = "#2C1A0E"
_HEADING_BG = "#F5EDE4"
_TOOLBAR_BG = "#F5EDE4"
_ROW_ALT_A  = "#FFFFFF"
_ROW_ALT_B  = "#FBF7F2"
_SEL_ROW    = "#FFF0E0"
_SHADOW     = "#D6CEC5"
_SUCCESS_HOVER = "#22703D"

# ── typography ───────────────────────────────────────────────────
_FONT_TITLE   = ("Segoe UI Semibold", 22)
_FONT_SECTION = ("Segoe UI Semibold", 14)
_FONT_BODY    = ("Segoe UI", 12)
_FONT_SMALL   = ("Segoe UI", 10)
_FONT_CAPTION  = ("Segoe UI", 9)
_FONT_BTN     = ("Segoe UI", 10)
_FONT_BTN_LG  = ("Segoe UI", 11, "bold")
_FONT_HEADING = ("Segoe UI", 10, "bold")
_FONT_TREE    = ("Segoe UI", 10)
_FONT_ENTRY   = ("Segoe UI", 11)


def money(v):
    try:
        return f"{int(v):,}".replace(",", ".")
    except (TypeError, ValueError):
        return v


FORMATTERS = {"money": money}


# ── helpers ──────────────────────────────────────────────────────
def _card_frame(parent, **kw):
    """White card container with subtle border and shadow illusion."""
    # outer shadow layer
    shadow = tk.Frame(parent, bg=_SHADOW, **kw)
    # border layer sits 1px inside the shadow
    border = tk.Frame(shadow, bg=_BORDER,
                      highlightbackground=_BORDER, highlightthickness=1)
    border.pack(padx=(0, 2), pady=(0, 2), fill="both", expand=True)
    # inner card
    inner = tk.Frame(border, bg=_CARD, padx=18, pady=14,
                     highlightbackground=_HEADING_BG, highlightthickness=1)
    inner.pack(padx=1, pady=1, fill="both", expand=True)
    return shadow, inner


def _accent_button(parent, text, command, large=False):
    """Coffee-brown button that stands out, with enhanced hover."""
    font = _FONT_BTN_LG if large else _FONT_BTN
    btn = tk.Button(parent, text=text, command=command, bg=ACCENT, fg=_BTN_FG,
                    activebackground=_HOVER, activeforeground=_BTN_FG,
                    font=font, relief="flat", cursor="hand2",
                    padx=26, pady=6 if large else 4, bd=0,
                    highlightbackground=_HOVER, highlightthickness=0)
    btn.bind("<Enter>", lambda e: btn.configure(bg=_HOVER, relief="flat", bd=2))
    btn.bind("<Leave>", lambda e: btn.configure(bg=ACCENT, relief="flat", bd=0))
    return btn


def _success_button(parent, text, command, large=False):
    """Green button for positive / success actions."""
    font = _FONT_BTN_LG if large else _FONT_BTN
    btn = tk.Button(parent, text=text, command=command,
                    bg=_SUCCESS, fg=_BTN_FG,
                    activebackground=_SUCCESS_HOVER, activeforeground=_BTN_FG,
                    font=font, relief="flat", cursor="hand2",
                    padx=26, pady=6 if large else 4, bd=0,
                    highlightbackground=_SUCCESS_HOVER, highlightthickness=0)
    btn.bind("<Enter>", lambda e: btn.configure(bg=_SUCCESS_HOVER, relief="flat", bd=2))
    btn.bind("<Leave>", lambda e: btn.configure(bg=_SUCCESS, relief="flat", bd=0))
    return btn


def _subtle_button(parent, text, command):
    """Neutral gray button for secondary actions."""
    btn = tk.Button(parent, text=text, command=command, bg="#E5E7EB", fg="#374151",
                    activebackground="#D1D5DB", activeforeground="#1F2937",
                    font=_FONT_BTN, relief="flat", cursor="hand2",
                    padx=16, pady=4, bd=0,
                    highlightbackground="#D1D5DB", highlightthickness=0)
    btn.bind("<Enter>", lambda e: btn.configure(bg="#D1D5DB", relief="flat", bd=2))
    btn.bind("<Leave>", lambda e: btn.configure(bg="#E5E7EB", relief="flat", bd=0))
    return btn


def _danger_button(parent, text, command):
    """Red button for destructive actions."""
    btn = tk.Button(parent, text=text, command=command, bg=_ERROR, fg=_BTN_FG,
                    activebackground="#B71C1C", activeforeground=_BTN_FG,
                    font=_FONT_BTN, relief="flat", cursor="hand2",
                    padx=16, pady=4, bd=0,
                    highlightbackground="#B71C1C", highlightthickness=0)
    btn.bind("<Enter>", lambda e: btn.configure(bg="#B71C1C", relief="flat", bd=2))
    btn.bind("<Leave>", lambda e: btn.configure(bg=_ERROR, relief="flat", bd=0))
    return btn


def _section_label(parent, text, bg=None):
    """Section header with accent color and bottom line."""
    bg = bg or BG
    frm = tk.Frame(parent, bg=bg)
    tk.Label(frm, text=text, bg=bg, fg=ACCENT,
             font=_FONT_SECTION).pack(side="left")
    return frm


def _focus_ring_bind(widget):
    """Bind focus/blur events to show/hide a 2px accent ring on entries."""
    widget.bind("<FocusIn>",  lambda e: widget.configure(highlightthickness=2))
    widget.bind("<FocusOut>", lambda e: widget.configure(highlightthickness=1))


def _style_treeview():
    """Configure the ttk.Treeview style globally for a polished look."""
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Polished.Treeview",
                    background=_ROW_ALT_A,
                    foreground=FG,
                    fieldbackground=_ROW_ALT_A,
                    rowheight=32,
                    font=_FONT_TREE,
                    borderwidth=0,
                    relief="flat")
    style.configure("Polished.Treeview.Heading",
                    background=_HEADING_BG,
                    foreground=FG,
                    font=_FONT_HEADING,
                    relief="flat",
                    borderwidth=0,
                    padding=(8, 6))
    style.map("Polished.Treeview.Heading",
              background=[("active", _TOOLBAR_BG)])
    style.map("Polished.Treeview",
              background=[("selected", _SEL_ROW)],
              foreground=[("selected", FG)])
    # Combobox polish
    style.configure("Pill.TCombobox",
                    background=_CARD,
                    fieldbackground=_CARD,
                    foreground=FG,
                    arrowcolor=ACCENT,
                    borderwidth=1,
                    relief="solid",
                    padding=(8, 4))
    style.map("Pill.TCombobox",
              fieldbackground=[("readonly", _CARD)],
              bordercolor=[("focus", ACCENT)])
    # Scrollbar polish
    style.configure("Coffee.Vertical.TScrollbar",
                    gripcount=0,
                    background=_BORDER,
                    troughcolor=_HEADING_BG,
                    borderwidth=0,
                    arrowsize=14)
    style.map("Coffee.Vertical.TScrollbar",
              background=[("active", ACCENT), ("!active", _BORDER)])

_treeview_styled = False


def _ensure_tree_style():
    global _treeview_styled
    if not _treeview_styled:
        _style_treeview()
        _treeview_styled = True


# ── dialog icon helpers ──────────────────────────────────────────
_DIALOG_ICONS = {
    "default": "📝",
    "add":     "➕",
    "edit":    "✏️",
    "delete":  "🗑️",
    "search":  "🔍",
    "money":   "💰",
    "user":    "👤",
    "config":  "⚙️",
}


def _pick_dialog_icon(title):
    """Choose an icon based on dialog title keywords."""
    t = title.lower()
    if any(w in t for w in ("thêm", "tạo", "add", "new")):
        return _DIALOG_ICONS["add"]
    if any(w in t for w in ("sửa", "edit", "cập nhật", "update")):
        return _DIALOG_ICONS["edit"]
    if any(w in t for w in ("xóa", "xoá", "delete", "remove")):
        return _DIALOG_ICONS["delete"]
    if any(w in t for w in ("tìm", "search", "lọc", "filter")):
        return _DIALOG_ICONS["search"]
    if any(w in t for w in ("tiền", "thanh toán", "pay", "money")):
        return _DIALOG_ICONS["money"]
    if any(w in t for w in ("người", "nhân viên", "user", "staff")):
        return _DIALOG_ICONS["user"]
    if any(w in t for w in ("cài", "config", "setting")):
        return _DIALOG_ICONS["config"]
    return _DIALOG_ICONS["default"]


# ── ask_dialog ───────────────────────────────────────────────────
def ask_dialog(parent, title, fields, defaults=None):
    """Hộp thoại nhập. fields: [(key, label, kind, choices)], kind: text|int|choice. Trả dict hoặc None."""
    defaults = defaults or {}
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.transient(parent.winfo_toplevel())
    dlg.grab_set()
    dlg.configure(bg=_CARD, padx=24, pady=20)
    dlg.resizable(False, False)
    dlg.overrideredirect(False)

    # shadow backdrop illusion — dark border around dialog
    dlg.configure(highlightbackground=_SHADOW, highlightthickness=3,
                  highlightcolor=_SHADOW)

    # icon for dialog
    icon = _pick_dialog_icon(title)

    # title header with icon
    hdr_frame = tk.Frame(dlg, bg=_CARD)
    hdr_frame.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
    tk.Label(hdr_frame, text=icon, bg=_CARD,
             font=("Segoe UI", 20)).pack(side="left", padx=(0, 10))
    tk.Label(hdr_frame, text=title, bg=_CARD, fg=FG,
             font=("Segoe UI Semibold", 15)).pack(side="left")

    # gold accent bar under title
    gold_bar = tk.Frame(dlg, bg=_GOLD, height=2)
    gold_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 14))

    vars_ = {}
    for i, (key, label, kind, *rest) in enumerate(fields):
        tk.Label(dlg, text=label, bg=_CARD, fg=FG,
                 font=_FONT_BODY).grid(row=i + 2, column=0, sticky="w",
                                       pady=8, padx=(0, 20))
        v = tk.StringVar(value=str(defaults.get(key, "")))
        vars_[key] = v
        if kind == "choice":
            choices = rest[0]
            w = ttk.Combobox(dlg, textvariable=v,
                             values=[c[0] for c in choices],
                             state="readonly", width=30,
                             style="Pill.TCombobox")
            if not v.get() and choices:
                v.set(choices[0][0])
        else:
            w = tk.Entry(dlg, textvariable=v, width=33,
                         show="*" if kind == "password" else "",
                         font=_FONT_ENTRY, relief="solid", bd=1,
                         bg=_INPUT_BG, highlightcolor=ACCENT,
                         highlightthickness=1)
            _focus_ring_bind(w)
        w.grid(row=i + 2, column=1, pady=8, ipady=4, padx=(0, 4))
    result = {}

    def ok():
        out = {}
        for key, label, kind, *rest in fields:
            val = vars_[key].get().strip()
            if kind == "choice":
                val = dict(rest[0]).get(val, val)
            out[key] = val
        result.update(out)
        dlg.destroy()

    bar = tk.Frame(dlg, bg=_CARD)
    bar.grid(row=len(fields) + 2, column=0, columnspan=2,
             pady=(20, 0), sticky="e")
    _subtle_button(bar, "  Hủy  ", dlg.destroy).pack(side="left", padx=(0, 10))
    _accent_button(bar, "  Đồng ý  ", ok).pack(side="left")

    # center on parent
    dlg.update_idletasks()
    pw = parent.winfo_toplevel()
    x = pw.winfo_x() + (pw.winfo_width() - dlg.winfo_reqwidth()) // 2
    y = pw.winfo_y() + (pw.winfo_height() - dlg.winfo_reqheight()) // 2
    dlg.geometry(f"+{max(0,x)}+{max(0,y)}")

    dlg.wait_window()
    return result or None


# ── Panel base ───────────────────────────────────────────────────
class Panel(ttk.Frame):
    """Lớp cơ sở: nhận push từ server, chế độ chỉ xem cho Admin giám sát."""
    refresh_on = ()

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        _ensure_tree_style()

    def on_push(self, msg_type, payload):
        if msg_type in self.refresh_on:
            self.refresh()

    def refresh(self):
        pass


# ── ListPanel ────────────────────────────────────────────────────
class ListPanel(Panel):
    def __init__(self, parent, app, request, columns, actions=(), params=None, refresh_on=(), choice=None,
                 info=None, auto_sec=None, hint=None):
        super().__init__(parent, app)
        self.request, self.columns, self.actions = request, columns, actions
        self.params, self.refresh_on, self.choice, self.info, self.auto_sec = params or {}, refresh_on, choice, info, auto_sec
        self.rows = []

        # ── toolbar ──
        toolbar = tk.Frame(self, bg=_TOOLBAR_BG, padx=12, pady=10,
                           highlightbackground=_BORDER, highlightthickness=1)
        toolbar.pack(fill="x", pady=(0, 10))

        self.btns = []
        if choice:
            self.choice_var = tk.StringVar(value=choice[1][0][0])
            cb = ttk.Combobox(toolbar, textvariable=self.choice_var,
                              values=[c[0] for c in choice[1]],
                              state="readonly", width=14,
                              style="Pill.TCombobox")
            cb.pack(side="left", padx=(0, 10))
            cb.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        b_refresh = _subtle_button(toolbar, "🔄 Làm mới", self.refresh)
        b_refresh.pack(side="left", padx=(0, 12))

        for a in actions:
            btn = _accent_button(toolbar, a["label"], lambda a=a: self.run_action(a))
            btn.pack(side="left", padx=5)
            self.btns.append(btn)

        # ── info bar ──
        self.info_var = tk.StringVar(value=hint or "")
        info_lbl = tk.Label(self, textvariable=self.info_var, bg=BG, fg=ACCENT,
                            font=_FONT_SMALL, anchor="w", padx=6)
        info_lbl.pack(fill="x", pady=(0, 4))

        # ── treeview in card ──
        card_outer, card_inner = _card_frame(self)
        card_outer.pack(fill="both", expand=True)
        card_inner.configure(padx=0, pady=0)

        self.tree = ttk.Treeview(card_inner,
                                 columns=[c[0] for c in columns],
                                 show="headings", selectmode="browse",
                                 style="Polished.Treeview")
        for c in columns:
            self.tree.heading(c[0], text=c[1])
            self.tree.column(c[0], width=c[2], anchor="w")
        sb = ttk.Scrollbar(card_inner, orient="vertical",
                           command=self.tree.yview,
                           style="Coffee.Vertical.TScrollbar")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.tag_configure("late", foreground=_ERROR,
                                font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure("oddrow", background=_ROW_ALT_B)
        self.tree.tag_configure("evenrow", background=_ROW_ALT_A)

        # ── status bar ──
        status_bar = tk.Frame(self, bg=BG)
        status_bar.pack(fill="x", pady=(0, 0))
        # top-border separator
        tk.Frame(status_bar, bg=_BORDER, height=1).pack(fill="x")

        self.count_var = tk.StringVar(value="")
        tk.Label(status_bar, textvariable=self.count_var, bg=BG, fg=_SECONDARY,
                 font=_FONT_CAPTION, anchor="e",
                 padx=6, pady=3).pack(fill="x")

        if app.readonly:
            self.info_var.set("⚠️  Chế độ giám sát: chỉ xem giao diện, không thực hiện thao tác nghiệp vụ.")
            for btn in self.btns:
                btn.configure(state="disabled", bg="#D1D5DB", cursor="arrow")
            b_refresh.configure(state="disabled", cursor="arrow")
        else:
            self.refresh()
            if auto_sec:
                self._auto()

    def _auto(self):
        if self.winfo_exists():
            self.refresh()
            self.after(self.auto_sec * 1000, self._auto)

    def refresh(self):
        if self.app.readonly or not self.winfo_exists():
            return
        params = dict(self.params)
        if self.choice:
            params[self.choice[0]] = dict(self.choice[1]).get(self.choice_var.get())
        self.app.call(self.request, params, self._fill)

    def _fill(self, msg):
        if msg["type"] != "ACK" or not self.winfo_exists():
            return
        sel = self.tree.selection()
        keep = self.tree.item(sel[0], "values")[0] if sel else None
        self.tree.delete(*self.tree.get_children())
        self.rows = msg["payload"].get("rows", [])
        for idx, r in enumerate(self.rows):
            vals = []
            for c in self.columns:
                v = r.get(c[0], "")
                if len(c) > 3:
                    v = FORMATTERS[c[3]](v)
                vals.append(v)
            row_tag = "late" if r.get("late") else ("oddrow" if idx % 2 else "evenrow")
            self.tree.insert("", "end", values=vals, tags=(row_tag,))
        if self.info:
            self.info_var.set(self.info(msg["payload"]))
        self.count_var.set(f"Tổng: {len(self.rows)} dòng")
        if keep is not None:
            for iid in self.tree.get_children():
                if str(self.tree.item(iid, "values")[0]) == str(keep):
                    self.tree.selection_set(iid)

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.rows[self.tree.index(sel[0])]

    def run_action(self, a):
        row = self.selected() if a.get("row", True) else {}
        if row is None:
            messagebox.showinfo("Chưa chọn", "Hãy chọn một dòng trong danh sách trước.")
            return
        payload = a["payload"](row) if a.get("payload") else {}
        if a.get("ask"):
            defaults = {k: row.get(v, "") for k, v in a.get("defaults", {}).items()}
            extra = ask_dialog(self, a["label"], a["ask"], defaults)
            if extra is None:
                return
            payload = {**payload, **extra}
        if a.get("confirm") and not messagebox.askyesno("Xác nhận", a["confirm"]):
            return

        def done(msg):
            if msg["type"] == "ACK":
                if a.get("show"):
                    messagebox.showinfo(a["label"], str(msg["payload"].get(a["show"], "Xong")))
                self.refresh()
            else:
                messagebox.showerror("Không thực hiện được", msg["payload"].get("message", "Lỗi"))
        self.app.call(a["type"], payload, done)


# ── FormPanel ────────────────────────────────────────────────────
class FormPanel(Panel):
    def __init__(self, parent, app, fields, submit, label="Gửi", success="Thành công", extra=None, reset=True):
        super().__init__(parent, app)
        self.fields, self.submit, self.success, self.extra, self.reset = fields, submit, success, extra or {}, reset
        self.vars = {}

        card_outer, card_inner = _card_frame(self)
        card_outer.pack(anchor="nw", pady=10, fill="x")

        # section heading
        hdr = tk.Frame(card_inner, bg=_CARD)
        hdr.pack(anchor="w", pady=(0, 4), fill="x")
        tk.Label(hdr, text="📝", bg=_CARD,
                 font=("Segoe UI", 16)).pack(side="left", padx=(0, 8))
        tk.Label(hdr, text="Nhập thông tin", bg=_CARD, fg=FG,
                 font=_FONT_SECTION).pack(side="left")
        tk.Frame(card_inner, bg=_GOLD, height=2).pack(fill="x", pady=(0, 12))

        form = tk.Frame(card_inner, bg=_CARD)
        form.pack(anchor="nw", padx=4)

        for i, (key, text, kind, *rest) in enumerate(fields):
            tk.Label(form, text=text, bg=_CARD, fg=FG,
                     font=_FONT_BODY).grid(row=i, column=0, sticky="w",
                                           pady=8, padx=(0, 20))
            v = tk.StringVar()
            self.vars[key] = v
            if kind == "choice":
                w = ttk.Combobox(form, textvariable=v,
                                 values=[c[0] for c in rest[0]],
                                 state="readonly", width=30,
                                 style="Pill.TCombobox")
                v.set(rest[0][0][0])
            else:
                w = tk.Entry(form, textvariable=v, width=33,
                             show="*" if kind == "password" else "",
                             font=_FONT_ENTRY, relief="solid", bd=1,
                             bg=_INPUT_BG, highlightcolor=ACCENT,
                             highlightthickness=1)
                _focus_ring_bind(w)
            w.grid(row=i, column=1, pady=8, ipady=4)

        btn_frame = tk.Frame(card_inner, bg=_CARD)
        btn_frame.pack(anchor="w", pady=(14, 6))
        self.btn = _accent_button(btn_frame, f"  {label}  ", self.send, large=True)
        self.btn.pack(side="left")

        self.msg = tk.StringVar()
        self.msg_lbl = tk.Label(self, textvariable=self.msg, bg=BG, fg=ACCENT,
                                font=_FONT_SMALL, wraplength=520, anchor="w", padx=6)
        self.msg_lbl.pack(fill="x", pady=(6, 0))

        if app.readonly:
            self.btn.configure(state="disabled", bg="#D1D5DB", cursor="arrow")
            self.msg.set("⚠️  Chế độ giám sát: chỉ xem giao diện, không thực hiện thao tác nghiệp vụ.")

    def send(self):
        payload = dict(self.extra)
        for key, _, kind, *rest in self.fields:
            val = self.vars[key].get().strip()
            payload[key] = dict(rest[0]).get(val, val) if kind == "choice" else val

        def done(msg):
            if not self.winfo_exists():
                return
            if msg["type"] == "ACK":
                self.msg.set(f"✅  {self.success}")
                self.msg_lbl.configure(fg=_SUCCESS)
                if self.reset:
                    for key, _, kind, *rest in self.fields:
                        if kind != "choice":
                            self.vars[key].set("")
            else:
                self.msg.set("❌  Lỗi: " + msg["payload"].get("message", ""))
                self.msg_lbl.configure(fg=_ERROR)
        self.app.call(self.submit, payload, done)


# ── ActionPanel ──────────────────────────────────────────────────
class ActionPanel(Panel):
    """Một nút bấm gửi một message (ví dụ: Gọi nhân viên, Kiểm tra CSDL)."""

    def __init__(self, parent, app, text, label, request, show=None, success="Đã gửi"):
        super().__init__(parent, app)

        card_outer, card_inner = _card_frame(self)
        card_outer.pack(anchor="nw", pady=10, fill="x")

        # description with improved typography
        tk.Label(card_inner, text=text, bg=_CARD, fg=FG,
                 font=_FONT_BODY, wraplength=520, justify="left").pack(
                     anchor="w", pady=(0, 14))

        self.msg = tk.StringVar()
        self.btn = _accent_button(card_inner, f"  {label}  ",
                                  lambda: app.call(request, {}, self.done), large=True)
        self.btn.pack(anchor="w", pady=(0, 10))

        self.msg_lbl = tk.Label(card_inner, textvariable=self.msg, bg=_CARD, fg=ACCENT,
                                font=_FONT_SMALL, wraplength=520, anchor="w")
        self.msg_lbl.pack(anchor="w")
        self.show, self.success = show, success

        if app.readonly:
            self.btn.configure(state="disabled", bg="#D1D5DB", cursor="arrow")
            self.msg.set("⚠️  Chế độ giám sát: chỉ xem giao diện, không thực hiện thao tác nghiệp vụ.")

    def done(self, msg):
        if not self.winfo_exists():
            return
        if msg["type"] == "ACK":
            self.msg.set(f"✅  {str(msg['payload'].get(self.show)) if self.show else self.success}")
            self.msg_lbl.configure(fg=_SUCCESS)
        else:
            self.msg.set("❌  Lỗi: " + msg["payload"].get("message", ""))
            self.msg_lbl.configure(fg=_ERROR)


# ── LogPanel ─────────────────────────────────────────────────────
class LogPanel(Panel):
    """Nhật ký thông báo server đẩy xuống trong phiên này (món sẵn sàng, cảnh báo trễ...)."""

    # emoji prefixes for log entry types
    _TYPE_EMOJI = {
        "ITEM_READY": "☕",
        "ORDER_NEW": "🛎️",
        "WARN_LATE": "⏰",
        "ERROR": "❌",
        "INFO": "ℹ️",
    }

    def __init__(self, parent, app, types, title):
        super().__init__(parent, app)
        self.types, self.refresh_on = types, types

        header = _section_label(self, f"📋  {title}")
        header.pack(fill="x", pady=(0, 4))
        # gold accent line
        tk.Frame(self, bg=_GOLD, height=2).pack(fill="x", pady=(0, 10))

        card_outer, card_inner = _card_frame(self)
        card_outer.pack(fill="both", expand=True)
        card_inner.configure(padx=2, pady=2)

        self.box = tk.Listbox(card_inner, height=18, font=_FONT_BODY,
                              bg=_CARD, fg=FG, selectbackground=_SEL_ROW,
                              selectforeground=FG, relief="flat", bd=0,
                              highlightthickness=0, activestyle="none")
        self.box.pack(fill="both", expand=True)

        self.empty_lbl = tk.Label(card_inner,
                                  text="Chưa có thông báo nào trong phiên này.",
                                  bg=_CARD, fg=_SECONDARY,
                                  font=("Segoe UI", 10, "italic"))
        self.refresh()

    def _colorize(self, idx, entry_type):
        """Color log entry based on type for quick visual scanning."""
        if "LATE" in entry_type or "WARN" in entry_type:
            self.box.itemconfig(idx, fg="#E65100")
        elif "ERROR" in entry_type:
            self.box.itemconfig(idx, fg=_ERROR)
        elif "READY" in entry_type:
            self.box.itemconfig(idx, fg=_SUCCESS)
        # alternating background always
        if idx % 2:
            self.box.itemconfig(idx, bg=_ROW_ALT_B)

    def refresh(self):
        if not self.winfo_exists():
            return
        self.box.delete(0, "end")
        count = 0
        for t, text in reversed(self.app.notifications):
            if t in self.types:
                # prepend emoji based on type
                emoji = self._TYPE_EMOJI.get(t, "📌")
                self.box.insert("end", f" {emoji}  {text}")
                self._colorize(count, t)
                count += 1
        if count == 0:
            self.empty_lbl.place(relx=0.5, rely=0.4, anchor="center")
        else:
            self.empty_lbl.place_forget()
