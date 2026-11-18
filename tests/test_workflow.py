"""Kiểm thử tích hợp: chạy server thật trên cổng thử và đi qua 2 workflow + phân quyền.
Chạy:  python -m unittest tests.test_workflow -v
"""
import os
import socket
import tempfile
import time
import unittest

from database.db import Database
from protocol.messages import MessageStream
from server import server as srv


class Client:
    def __init__(self, port):
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=5)
        self.st = MessageStream(self.sock)
        self.n = 0
        self.pushes = []

    def call(self, t, **payload):
        self.n += 1
        self.st.send(t, payload, self.n)
        while True:
            m = self.st.recv()
            if m["type"] == "PING":
                continue
            if m.get("id") == self.n:
                return m
            self.pushes.append(m)

    def ok(self, t, **payload):
        m = self.call(t, **payload)
        assert m["type"] == "ACK", m
        return m["payload"]

    def err(self, t, **payload):
        m = self.call(t, **payload)
        assert m["type"] == "ERROR", m
        return m["payload"]["code"]

    def drain(self, wait=0.4):
        self.sock.settimeout(wait)
        try:
            while True:
                m = self.st.recv()
                if m is None:
                    break
                self.pushes.append(m)
        except (socket.timeout, OSError):
            pass
        self.sock.settimeout(5)

    def got(self, t):
        return [m for m in self.pushes if m["type"] == t]


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class TestWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()
        cls.lan, cls.net = free_port(), free_port()
        cfg = {"host": "127.0.0.1", "port_lan": cls.lan, "port_internet": cls.net, "ssl_enabled": False,
               "db_path": os.path.join(cls.tmp, "t.db"), "late_scan_sec": 0.3}
        cls.ctx, cls.stop = srv.start(cfg, Database(cfg["db_path"]))
        time.sleep(0.2)

    @classmethod
    def tearDownClass(cls):
        cls.stop()

    def staff(self, user):
        c = Client(self.lan)
        c.ok("LOGIN", username=user, password=user + "123")
        return c

    def test_1_workflow_dat_mon(self):
        khach = Client(self.lan)
        khach.ok("GUEST_CONNECT", table_id=3)
        pv, bep, tn = self.staff("phucvu"), self.staff("phache"), self.staff("thungan")
        quanly, chu = self.staff("quanly"), self.staff("chuquan")
        menu = khach.ok("MENU_LIST")["rows"]
        # Khách gửi yêu cầu chọn món -> chỉ phục vụ nhận, bếp chưa thấy
        oid = khach.ok("ORDER_REQUEST", items=[{"menu_item_id": menu[0]["id"], "quantity": 2, "note": "ít đá"},
                                               {"menu_item_id": menu[1]["id"], "quantity": 1}])["order_id"]
        pv.drain(); bep.drain()
        self.assertTrue(pv.got("SERVICE_REQUEST_NEW"))
        self.assertEqual(bep.ok("KITCHEN_LIST")["rows"], [])
        # Phục vụ chuyển cho bếp
        self.assertEqual(len(pv.ok("SERVICE_REQUESTS")["rows"]), 1)
        pv.ok("ORDER_FORWARD", order_id=oid)
        bep.drain()
        self.assertTrue(bep.got("KITCHEN_NEW_ORDER"))
        items = bep.ok("KITCHEN_LIST")["rows"]
        self.assertEqual(len(items), 2)
        # Sai thứ tự trạng thái bị từ chối
        self.assertEqual(bep.err("ITEM_DONE", item_id=items[0]["item_id"]), "BAD_STATE")
        for it in items:
            bep.ok("ITEM_START", item_id=it["item_id"])
            bep.ok("ITEM_DONE", item_id=it["item_id"])
        pv.drain()
        self.assertTrue(pv.got("ORDER_READY"))
        khach.drain()
        self.assertEqual(khach.got("ORDER_UPDATED")[-1]["payload"]["status"], "Sẵn sàng")
        # Khách yêu cầu thanh toán -> thu ngân nhận
        khach.ok("PAYMENT_REQUEST", order_id=oid)
        tn.drain()
        self.assertTrue(tn.got("PAYMENT_REQUESTED"))
        pending = tn.ok("PAYMENT_PENDING", only_requested=True)["rows"]
        self.assertEqual(pending[0]["total"], 2 * menu[0]["price"] + menu[1]["price"])
        # Chủ quán xem được danh sách chờ (công nợ), phục vụ kiểm tra trạng thái
        self.assertEqual(len(chu.ok("PAYMENT_PENDING")["rows"]), 1)
        self.assertEqual(pv.ok("PAYMENT_STATUS_LIST")["rows"][0]["payment"], "Chưa thanh toán")
        tn.ok("PAYMENT_CONFIRM", order_id=oid, method="Tiền mặt")
        self.assertEqual(pv.ok("PAYMENT_STATUS_LIST")["rows"][0]["payment"], "Đã thanh toán")
        # Doanh thu: chủ quán xem được, quản lý KHÔNG
        self.assertGreater(chu.ok("REVENUE", period="day")["total"], 0)
        self.assertEqual(quanly.err("REVENUE", period="day"), "FORBIDDEN")
        self.assertEqual(quanly.err("OVERVIEW"), "FORBIDDEN")
        # Thống kê của quản lý
        self.assertTrue(quanly.ok("STATS_TOP_ITEMS")["rows"])
        self.assertGreaterEqual(quanly.ok("STATS_AVG_SERVICE")["rows"][0]["value"], 1)

    def test_2_canh_bao_tre(self):
        khach = Client(self.lan)
        khach.ok("GUEST_CONNECT", table_id=5)
        pv, bep, ql = self.staff("phucvu"), self.staff("phache"), self.staff("quanly")
        menu = khach.ok("MENU_LIST")["rows"]
        oid = khach.ok("ORDER_REQUEST", items=[{"menu_item_id": menu[2]["id"], "quantity": 1}])["order_id"]
        pv.ok("ORDER_FORWARD", order_id=oid)
        ql.ok("LATE_CONFIG_SET", minutes=0.1)   # 6 giây, áp dụng ngay không cần khởi động lại
        time.sleep(7.5)
        ql.drain(); bep.drain()
        self.assertTrue(ql.got("ALERT_LATE_ORDER"))
        self.assertTrue(bep.got("ALERT_LATE_ORDER"))
        self.assertTrue(ql.ok("LATE_LIST")["rows"])
        ql.ok("LATE_CONFIG_SET", minutes=10)

    def test_3_dat_ban(self):
        net = Client(self.net)
        # Cổng Internet chặn mọi thứ ngoài đặt bàn
        self.assertEqual(net.err("MENU_LIST"), "FORBIDDEN")
        self.assertEqual(net.err("LOGIN", username="admin", password="admin123"), "FORBIDDEN")
        self.assertEqual(net.err("RESERVATION_MY"), "NOT_LOGGED_IN")
        net.ok("CUSTOMER_REGISTER", phone="0901234567", full_name="Nguyễn An", password="matkhau1")
        self.assertEqual(net.err("CUSTOMER_REGISTER", phone="0901234567", full_name="X", password="matkhau1"), "DUPLICATE")
        self.assertEqual(net.err("CUSTOMER_LOGIN", phone="0901234567", password="sai"), "BAD_LOGIN")
        net.ok("CUSTOMER_LOGIN", phone="0901234567", password="matkhau1")
        self.assertEqual(net.err("RESERVATION_CREATE", guests=2, arrive_time="2020-01-01 10:00"), "BAD_REQUEST")
        future = time.strftime("%Y-%m-%d %H:%M", time.localtime(time.time() + 86400))
        ql = self.staff("quanly")
        rid = net.ok("RESERVATION_CREATE", guests=4, arrive_time=future)["id"]
        ql.drain()
        self.assertTrue(ql.got("RESERVATION_NEW"))
        self.assertEqual(ql.ok("RESERVATION_LIST")["rows"][0]["status"], "Chờ xác nhận")
        ql.ok("RESERVATION_DECIDE", id=rid, accept=True)   # Quản lý: Có
        net.drain()
        self.assertEqual(net.got("RESERVATION_UPDATED")[-1]["payload"]["status"], "Đã xác nhận")
        # Khách hủy đặt bàn
        net.ok("RESERVATION_CANCEL", id=rid)
        self.assertEqual(net.ok("RESERVATION_MY")["rows"][0]["status"], "Đã hủy")
        # Rate limit chống spam
        codes = [net.call("RESERVATION_CREATE", guests=2, arrive_time=future)["type"] for _ in range(6)]
        self.assertIn("ERROR", codes)

    def test_4_phan_quyen_va_admin(self):
        khach = Client(self.lan)
        self.assertEqual(khach.err("MENU_ADD", name="x", price=1), "NOT_LOGGED_IN")
        khach.ok("GUEST_CONNECT", table_id=1)
        self.assertEqual(khach.err("MENU_ADD", name="x", price=1), "FORBIDDEN")
        self.assertEqual(khach.err("ADMIN_STATUS"), "FORBIDDEN")
        ql, adm, chu = self.staff("quanly"), self.staff("admin"), self.staff("chuquan")
        ql.ok("MENU_ADD", name="Trà sữa", price=35000, category="Trà")
        self.assertEqual(adm.err("MENU_ADD", name="x", price=1), "FORBIDDEN")      # Admin không đụng nghiệp vụ
        self.assertEqual(adm.err("PAYMENT_CONFIRM", order_id=1, method="QR"), "FORBIDDEN")
        st = adm.ok("ADMIN_STATUS")["rows"]
        self.assertEqual(len(st), 11)
        self.assertTrue(adm.ok("ADMIN_REJECTED")["rows"])
        self.assertEqual(adm.ok("ADMIN_DB_CHECK")["result"], "ok")
        name = adm.ok("ADMIN_BACKUP")["name"]
        self.assertIn(name, [r["name"] for r in adm.ok("ADMIN_BACKUP_LIST")["rows"]])
        # Chủ quán: thêm / khóa tài khoản
        chu.ok("STAFF_ADD", username="nv1", password="nv1234", full_name="NV Một", role="PHUCVU")
        nid = [r["id"] for r in chu.ok("STAFF_LIST")["rows"] if r["username"] == "nv1"][0]
        c2 = Client(self.lan)
        c2.ok("LOGIN", username="nv1", password="nv1234")
        chu.ok("STAFF_LOCK", id=nid, locked=True)
        c3 = Client(self.lan)
        self.assertEqual(c3.err("LOGIN", username="nv1", password="nv1234"), "LOCKED")
        self.assertEqual(ql.err("STAFF_LIST"), "FORBIDDEN")
        # Ca làm việc
        d = time.strftime("%Y-%m-%d")
        pvid = [r["id"] for r in ql.ok("STAFF_BASIC")["rows"] if r["role"] == "PHUCVU"][0]
        ql.ok("SHIFT_ASSIGN", staff_id=pvid, date=d, shift_name="Sáng")
        self.assertEqual(ql.err("SHIFT_ASSIGN", staff_id=pvid, date=d, shift_name="Sáng"), "DUPLICATE")
        self.assertTrue(ql.ok("SHIFT_LIST", date=d)["rows"])


if __name__ == "__main__":
    unittest.main()
