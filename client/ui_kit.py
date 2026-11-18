"""Các panel dùng chung: danh sách + nút thao tác, biểu mẫu, hộp thoại nhập."""
import tkinter as tk
from tkinter import messagebox, ttk

BG, FG, ACCENT, DARK = "#f6f0e8", "#2b1d16", "#8a4f1f", "#2b1d16"


def money(v):
    try:
        return f"{int(v):,}".replace(",", ".")
    except (TypeError, ValueError):
        return v


FORMATTERS = {"money": money}


def ask_dialog(parent, title, fields, defaults=None):
    """Hộp thoại nhập. fields: [(key, label, kind, choices)], kind: text|int|choice. Trả dict hoặc None."""
    defaults = defaults or {}
    dlg = tk.Toplevel(parent)
    dlg.title(title)
    dlg.transient(parent.winfo_toplevel())
    dlg.grab_set()
    dlg.configure(bg=BG, padx=16, pady=12)
    vars_ = {}
    for i, (key, label, kind, *rest) in enumerate(fields):
        ttk.Label(dlg, text=label).grid(row=i, column=0, sticky="w", pady=4, padx=(0, 10))
        v = tk.StringVar(value=str(defaults.get(key, "")))
        vars_[key] = v
        if kind == "choice":
            choices = rest[0]
            w = ttk.Combobox(dlg, textvariable=v, values=[c[0] for c in choices], state="readonly", width=28)
            if not v.get() and choices:
                v.set(choices[0][0])
        else:
            w = ttk.Entry(dlg, textvariable=v, width=31, show="*" if kind == "password" else "")
        w.grid(row=i, column=1, pady=4)
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

    bar = ttk.Frame(dlg)
    bar.grid(row=len(fields), column=0, columnspan=2, pady=(10, 0))
    ttk.Button(bar, text="Đồng ý", command=ok).pack(side="left", padx=4)
    ttk.Button(bar, text="Hủy", command=dlg.destroy).pack(side="left", padx=4)
    dlg.wait_window()
    return result or None


class Panel(ttk.Frame):
    """Lớp cơ sở: nhận push từ server, chế độ chỉ xem cho Admin giám sát."""
    refresh_on = ()

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

    def on_push(self, msg_type, payload):
        if msg_type in self.refresh_on:
            self.refresh()

    def refresh(self):
        pass


class ListPanel(Panel):
    def __init__(self, parent, app, request, columns, actions=(), params=None, refresh_on=(), choice=None,
                 info=None, auto_sec=None, hint=None):
        super().__init__(parent, app)
        self.request, self.columns, self.actions = request, columns, actions
        self.params, self.refresh_on, self.choice, self.info, self.auto_sec = params or {}, refresh_on, choice, info, auto_sec
        self.rows = []
        bar = ttk.Frame(self)
        bar.pack(fill="x", pady=(0, 6))
        self.btns = []
        if choice:
            self.choice_var = tk.StringVar(value=choice[1][0][0])
            cb = ttk.Combobox(bar, textvariable=self.choice_var, values=[c[0] for c in choice[1]], state="readonly", width=12)
            cb.pack(side="left", padx=(0, 6))
            cb.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        b = ttk.Button(bar, text="Làm mới", command=self.refresh)
        b.pack(side="left", padx=(0, 12))
        for a in actions:
            btn = ttk.Button(bar, text=a["label"], command=lambda a=a: self.run_action(a))
            btn.pack(side="left", padx=3)
            self.btns.append(btn)
        self.info_var = tk.StringVar(value=hint or "")
        ttk.Label(self, textvariable=self.info_var, foreground=ACCENT).pack(anchor="w")
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings", selectmode="browse")
        for c in columns:
            self.tree.heading(c[0], text=c[1])
            self.tree.column(c[0], width=c[2], anchor="w")
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.tag_configure("late", foreground="#b00020")
        if app.readonly:
            self.info_var.set("Chế độ giám sát: chỉ xem giao diện, không thực hiện thao tác nghiệp vụ.")
            for btn in self.btns + [b]:
                btn.state(["disabled"])
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
        for r in self.rows:
            vals = []
            for c in self.columns:
                v = r.get(c[0], "")
                if len(c) > 3:
                    v = FORMATTERS[c[3]](v)
                vals.append(v)
            tags = ("late",) if r.get("late") else ()
            self.tree.insert("", "end", values=vals, tags=tags)
        if self.info:
            self.info_var.set(self.info(msg["payload"]))
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


class FormPanel(Panel):
    def __init__(self, parent, app, fields, submit, label="Gửi", success="Thành công", extra=None, reset=True):
        super().__init__(parent, app)
        self.fields, self.submit, self.success, self.extra, self.reset = fields, submit, success, extra or {}, reset
        self.vars = {}
        box = ttk.Frame(self)
        box.pack(anchor="nw", pady=8)
        for i, (key, text, kind, *rest) in enumerate(fields):
            ttk.Label(box, text=text).grid(row=i, column=0, sticky="w", pady=5, padx=(0, 12))
            v = tk.StringVar()
            self.vars[key] = v
            if kind == "choice":
                w = ttk.Combobox(box, textvariable=v, values=[c[0] for c in rest[0]], state="readonly", width=28)
                v.set(rest[0][0][0])
            else:
                w = ttk.Entry(box, textvariable=v, width=31, show="*" if kind == "password" else "")
            w.grid(row=i, column=1, pady=5)
        self.btn = ttk.Button(self, text=label, command=self.send)
        self.btn.pack(anchor="w", pady=8)
        self.msg = tk.StringVar()
        ttk.Label(self, textvariable=self.msg, foreground=ACCENT, wraplength=520).pack(anchor="w")
        if app.readonly:
            self.btn.state(["disabled"])
            self.msg.set("Chế độ giám sát: chỉ xem giao diện, không thực hiện thao tác nghiệp vụ.")

    def send(self):
        payload = dict(self.extra)
        for key, _, kind, *rest in self.fields:
            val = self.vars[key].get().strip()
            payload[key] = dict(rest[0]).get(val, val) if kind == "choice" else val

        def done(msg):
            if not self.winfo_exists():
                return
            if msg["type"] == "ACK":
                self.msg.set(self.success)
                if self.reset:
                    for key, _, kind, *rest in self.fields:
                        if kind != "choice":
                            self.vars[key].set("")
            else:
                self.msg.set("Lỗi: " + msg["payload"].get("message", ""))
        self.app.call(self.submit, payload, done)


class ActionPanel(Panel):
    """Một nút bấm gửi một message (ví dụ: Gọi nhân viên, Kiểm tra CSDL)."""

    def __init__(self, parent, app, text, label, request, show=None, success="Đã gửi"):
        super().__init__(parent, app)
        ttk.Label(self, text=text, wraplength=520).pack(anchor="w", pady=8)
        self.msg = tk.StringVar()
        self.btn = ttk.Button(self, text=label, command=lambda: app.call(request, {}, self.done))
        self.btn.pack(anchor="w", pady=6)
        ttk.Label(self, textvariable=self.msg, foreground=ACCENT, wraplength=520).pack(anchor="w")
        self.show, self.success = show, success
        if app.readonly:
            self.btn.state(["disabled"])
            self.msg.set("Chế độ giám sát: chỉ xem giao diện, không thực hiện thao tác nghiệp vụ.")

    def done(self, msg):
        if not self.winfo_exists():
            return
        if msg["type"] == "ACK":
            self.msg.set(str(msg["payload"].get(self.show)) if self.show else self.success)
        else:
            self.msg.set("Lỗi: " + msg["payload"].get("message", ""))


class LogPanel(Panel):
    """Nhật ký thông báo server đẩy xuống trong phiên này (món sẵn sàng, cảnh báo trễ...)."""

    def __init__(self, parent, app, types, title):
        super().__init__(parent, app)
        self.types, self.refresh_on = types, types
        ttk.Label(self, text=title, foreground=ACCENT).pack(anchor="w", pady=(0, 6))
        self.box = tk.Listbox(self, height=18, font=("Segoe UI", 11))
        self.box.pack(fill="both", expand=True)
        self.refresh()

    def refresh(self):
        if not self.winfo_exists():
            return
        self.box.delete(0, "end")
        for t, text in reversed(self.app.notifications):
            if t in self.types:
                self.box.insert("end", text)
