"""Chạy thử giao diện Tkinter với server thật (cần màn hình ảo nếu chạy trên server không có màn hình):
    xvfb-run -a python tests/gui_smoke.py
Mở lần lượt mọi phân hệ -> chức năng -> chức năng con của từng vai trò và báo lỗi nếu có."""
import os
import sys
import tempfile
import time
import tkinter as tk

sys.path.insert(0, os.getcwd())
from client.app import App  # noqa: E402
from client.modules import modules_for  # noqa: E402
import socket  # noqa: E402
import subprocess  # noqa: E402
from tests.test_workflow import free_port  # noqa: E402

SERVER_CODE = """
import sys, time
sys.path.insert(0, '.')
from database.db import Database
from server import server as srv
cfg = {'host': '127.0.0.1', 'port_lan': %d, 'port_internet': %d, 'ssl_enabled': False, 'db_path': %r}
srv.start(cfg, Database(cfg['db_path']))
time.sleep(600)
"""

errors = []


def spin(root, sec=0.5):
    end = time.time() + sec
    while time.time() < end:
        root.update()
        time.sleep(0.01)


def wait_until(root, cond, sec=6):
    end = time.time() + sec
    while time.time() < end and not cond():
        root.update()
        time.sleep(0.01)
    return cond()


def main():
    lan, net = free_port(), free_port()
    cfg = {"host": "127.0.0.1", "port_lan": lan, "port_internet": net, "ssl_enabled": False, "internet_ssl": False,
           "server_address": "127.0.0.1", "db_path": os.path.join(tempfile.mkdtemp(), "g.db")}
    # Server chạy ở tiến trình riêng như khi dùng thật (GUI và server chung tiến trình sẽ bị GC của Tk làm treo)
    proc = subprocess.Popen([sys.executable, "-c", SERVER_CODE % (lan, net, cfg["db_path"])], cwd=os.getcwd())
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", lan), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)
    root = tk.Tk()
    root.report_callback_exception = lambda *a: errors.append(a[1])
    app = App(root, cfg)
    checked = 0

    def visit(role_label):
        nonlocal checked
        for code, name, funcs in modules_for(app.role_key):
            app.open_module(code, name, funcs)
            spin(root, 0.1)
            for fn, cons in funcs:
                for label, factory in cons:
                    holder = tk.Frame(root)
                    try:
                        p = factory(holder, app)
                        p.pack()
                        spin(root, 0.15)
                        checked += 1
                    except Exception as e:  # noqa: BLE001
                        errors.append(f"{role_label}/{code}/{label}: {e!r}")
                    finally:
                        holder.destroy()
        app.show_home()
        spin(root, 0.2)

    for user in ("admin", "quanly", "chuquan", "thungan", "phucvu", "phache"):
        app.u_var.set(user)
        app.p_var.set(user + "123")
        app.login_staff()
        wait_until(root, lambda: app.role)
        if not app.role:
            print("ERRORS:", errors)
        assert app.role, f"đăng nhập {user} thất bại: {app.login_msg.get()}"
        visit(user)
        app.logout()
        spin(root, 0.1)
    app.table_var.set(2)
    app.login_guest()
    wait_until(root, lambda: app.role)
    assert app.role_key == "KHACH_BAN"
    visit("khach_ban")
    app.logout()
    spin(root, 0.1)
    # khách tài khoản: đăng ký bằng giao thức rồi đăng nhập
    app.connect("127.0.0.1", net, False)
    app.conn.send("CUSTOMER_REGISTER", {"phone": "0911222333", "full_name": "Khách Thử", "password": "abc12345"}, lambda m: None)
    spin(root, 0.5)
    app.ph_var.set("0911222333")
    app.cp_var.set("abc12345")
    app.login_customer()
    wait_until(root, lambda: app.role)
    assert app.role_key == "KHACH_TK", app.login_msg.get()
    visit("khach_tk")
    print(f"Đã mở thành công {checked} chức năng con. Lỗi: {len(errors)}")
    for e in errors:
        print(" -", e)
    root.destroy()
    proc.kill()
    sys.exit(1 if errors else 0)


main()
