"""Khai báo 11 phân hệ -> chức năng -> chức năng con (khớp sơ đồ phân rã trong slide).
Mỗi chức năng con là một panel (giao diện thao tác trực tiếp với người dùng)."""
from client.order_panel import OrderPanel
from client.ui_kit import ActionPanel, FormPanel, ListPanel, LogPanel

A = ("ADMIN",)
QL, CQ, TN, PV, PC, KB, KT = "QUANLY", "CHUQUAN", "THUNGAN", "PHUCVU", "PHACHE", "KHACH_BAN", "KHACH_TK"


def LP(**kw):
    return lambda p, a: ListPanel(p, a, **kw)


def FP(**kw):
    return lambda p, a: FormPanel(p, a, **kw)


def AP(**kw):
    return lambda p, a: ActionPanel(p, a, **kw)


def LG(types, title):
    return lambda p, a: LogPanel(p, a, types, title)


def act(label, type_, key=None, **kw):
    d = {"label": label, "type": type_}
    if key:
        d["payload"] = lambda r, key=key: {key: r[key]}
    d.update(kw)
    return d


MENU_COLS = [("name", "Món", 200), ("category", "Nhóm", 90), ("price", "Giá (đ)", 90, "money"),
             ("state", "Tình trạng", 90), ("description", "Mô tả", 280)]
ORDER_COLS = [("order_id", "Đơn", 55), ("table", "Bàn", 70), ("items", "Món", 330), ("total", "Tổng (đ)", 90, "money"),
              ("status", "Trạng thái", 100), ("payment", "Thanh toán", 115), ("requested", "Yêu cầu TT", 85),
              ("created", "Giờ", 70)]
KV_COLS = [("key", "Chỉ số", 320), ("value", "Giá trị", 160)]
RES_COLS = [("id", "Mã", 50), ("name", "Khách", 150), ("phone", "SĐT", 110), ("guests", "Số khách", 70),
            ("arrive_time", "Giờ đến", 130), ("status", "Trạng thái", 100), ("created", "Gửi lúc", 90)]
STAFF_COLS = [("id", "ID", 45), ("username", "Tên đăng nhập", 130), ("full_name", "Họ tên", 160),
              ("role", "Vai trò", 100), ("state", "Trạng thái", 100)]
SHIFT_COLS = [("id", "Mã", 50), ("work_date", "Ngày", 100), ("shift_name", "Ca", 70), ("full_name", "Nhân viên", 170),
              ("role", "Vai trò", 100)]
MENU_FIELDS = [("name", "Tên món", "text"), ("description", "Mô tả", "text"), ("price", "Giá (đ)", "text"),
               ("category", "Nhóm", "text")]
SHIFTS = [("Sáng", "Sáng"), ("Chiều", "Chiều"), ("Tối", "Tối")]
METHODS = [("Tiền mặt", "Tiền mặt"), ("Chuyển khoản", "Chuyển khoản"), ("QR", "QR")]
ROLES = [("Quản lý", "QUANLY"), ("Thu ngân", "THUNGAN"), ("Phục vụ", "PHUCVU"), ("Pha chế", "PHACHE")]

# ---- các panel dùng lại ở nhiều chức năng con ----
p_status = LP(request="ADMIN_STATUS", auto_sec=5, columns=[
    ("code", "Mã", 60), ("name", "Phân hệ", 220), ("clients", "Client online", 100), ("last", "Hoạt động cuối", 120),
    ("errors", "Lỗi (5 phút)", 90), ("status", "Trạng thái", 120)])
p_sessions = LP(request="ADMIN_SESSIONS", auto_sec=5, columns=[
    ("id", "Session", 60), ("ip", "IP", 110), ("channel", "Kênh", 70), ("role", "Vai trò", 90), ("name", "Tên", 150),
    ("since", "Kết nối lúc", 100), ("idle", "Im lặng (giây)", 100)],
    actions=[act("Ngắt session đã chọn", "ADMIN_KICK", "id", confirm="Ngắt kết nối của session này?")])
p_config = LP(request="ADMIN_CONFIG_GET", columns=KV_COLS, actions=[
    {"label": "Đổi heartbeat", "type": "ADMIN_CONFIG_SET", "row": False, "ask": [
        ("heartbeat_interval_sec", "Chu kỳ (giây)", "text"), ("heartbeat_timeout_sec", "Hết hạn (giây)", "text")]}])
p_dbcheck = AP(text="Kiểm tra tính toàn vẹn của cơ sở dữ liệu SQLite trên server.", label="Kiểm tra ngay",
               request="ADMIN_DB_CHECK", show="result")
p_backup = LP(request="ADMIN_BACKUP_LIST", columns=[("name", "Bản sao lưu", 300), ("size_kb", "Dung lượng (KB)", 120)],
              actions=[{"label": "Sao lưu ngay", "type": "ADMIN_BACKUP", "row": False, "show": "name"},
                       act("Phục hồi bản đã chọn", "ADMIN_RESTORE", "name",
                           confirm="Phục hồi sẽ ghi đè dữ liệu hiện tại. Tiếp tục?")])
p_lock = LP(request="ADMIN_CUSTOMERS", columns=[("id", "ID", 50), ("phone", "SĐT", 120), ("full_name", "Họ tên", 180),
                                               ("state", "Trạng thái", 110)], actions=[
    {"label": "Khóa", "type": "ADMIN_LOCK_CUSTOMER", "payload": lambda r: {"id": r["id"], "locked": True}},
    {"label": "Mở khóa", "type": "ADMIN_LOCK_CUSTOMER", "payload": lambda r: {"id": r["id"], "locked": False}},
    {"label": "Chặn IP", "type": "ADMIN_BLOCK_IP", "row": False, "ask": [("ip", "Địa chỉ IP", "text")]}])
p_rejected = LP(request="ADMIN_REJECTED", columns=[("time", "Lúc", 100), ("ip", "IP", 110), ("role", "Vai trò", 90),
                                                  ("type", "Message", 180), ("code", "Mã lỗi", 120)])
p_menu_view = LP(request="MENU_LIST", columns=MENU_COLS, refresh_on=("MENU_UPDATED",))
p_menu_edit = LP(request="MENU_LIST", columns=MENU_COLS, refresh_on=("MENU_UPDATED",), actions=[
    {"label": "Sửa món", "type": "MENU_UPDATE", "payload": lambda r: {"id": r["id"]}, "ask": MENU_FIELDS,
     "defaults": {"name": "name", "description": "description", "price": "price", "category": "category"}},
    act("Xóa món", "MENU_DELETE", "id", confirm="Xóa món đã chọn khỏi thực đơn?"),
    {"label": "Đổi giá", "type": "MENU_SET_PRICE", "payload": lambda r: {"id": r["id"]},
     "ask": [("price", "Giá mới (đ)", "text")], "defaults": {"price": "price"}},
    {"label": "Bật/tắt còn hàng", "type": "MENU_SET_AVAILABLE",
     "payload": lambda r: {"id": r["id"], "available": not r["available"]}}])
p_order = lambda p, a: OrderPanel(p, a)  # noqa: E731
p_my_orders = LP(request="ORDER_MY", refresh_on=("ORDER_UPDATED", "PAYMENT_DONE"), columns=[
    ("order_id", "Đơn", 55), ("name", "Món", 200), ("quantity", "SL", 40), ("note", "Ghi chú", 130),
    ("item_status", "Trạng thái món", 130), ("order_status", "Trạng thái đơn", 110), ("payment", "Thanh toán", 110),
    ("requested", "Yêu cầu TT", 85)])
p_pay_send = LP(request="ORDER_MY", refresh_on=("ORDER_UPDATED", "PAYMENT_DONE"), columns=[
    ("order_id", "Đơn", 55), ("name", "Món", 220), ("quantity", "SL", 40), ("order_status", "Trạng thái đơn", 120),
    ("payment", "Thanh toán", 110), ("requested", "Yêu cầu TT", 85)],
    actions=[act("Gửi yêu cầu thanh toán cho đơn đã chọn", "PAYMENT_REQUEST", "order_id")])
p_call = AP(text="Gọi nhân viên phục vụ tới bàn của bạn.", label="Gọi nhân viên", request="CALL_STAFF",
            success="Đã gọi nhân viên, vui lòng chờ trong giây lát.")
p_res_form = FP(fields=[("guests", "Số khách", "text"), ("arrive_time", "Giờ đến (YYYY-MM-DD HH:MM)", "text")],
                submit="RESERVATION_CREATE", label="Đặt bàn", success="Đã gửi yêu cầu đặt bàn, chờ Quản lý xác nhận.")
p_res_mine = LP(request="RESERVATION_MY", refresh_on=("RESERVATION_UPDATED",), columns=[
    ("id", "Mã", 50), ("guests", "Số khách", 80), ("arrive_time", "Giờ đến", 140), ("status", "Trạng thái", 110),
    ("created", "Gửi lúc", 90)], actions=[act("Hủy đặt bàn đã chọn", "RESERVATION_CANCEL", "id",
                                                confirm="Hủy đặt bàn này?")])
p_info_account = lambda p, a: ActionPanel(p, a, "Đăng ký và đăng nhập tài khoản khách thực hiện ở màn hình đăng nhập "  # noqa: E731
                                          "(đăng xuất để đổi tài khoản).", "Đã đăng nhập", "SYNC_REQUEST", success="Phiên đăng nhập còn hiệu lực.")
p_res_manage = LP(request="RESERVATION_LIST", refresh_on=("RESERVATION_NEW",), columns=RES_COLS, actions=[
    {"label": "Xác nhận", "type": "RESERVATION_DECIDE", "payload": lambda r: {"id": r["id"], "accept": True}},
    {"label": "Từ chối", "type": "RESERVATION_DECIDE", "payload": lambda r: {"id": r["id"], "accept": False},
     "confirm": "Từ chối yêu cầu đặt bàn này?"}])
p_kitchen = LP(request="KITCHEN_LIST", auto_sec=15, refresh_on=("KITCHEN_NEW_ORDER", "KITCHEN_REFRESH", "ALERT_LATE_ORDER"),
               columns=[("table", "Bàn", 70), ("name", "Món", 200), ("quantity", "SL", 40), ("note", "Ghi chú", 150),
                        ("status", "Trạng thái", 90), ("received", "Nhận lúc", 80), ("wait_min", "Chờ (phút)", 80),
                        ("late", "Trễ", 60)],
               actions=[act("Bắt đầu làm món", "ITEM_START", "item_id"), act("Hoàn tất món", "ITEM_DONE", "item_id")])
p_svc_req = LP(request="SERVICE_REQUESTS", refresh_on=("SERVICE_REQUEST_NEW",), columns=ORDER_COLS[:5], actions=[
    act("Chuyển đơn cho bếp", "ORDER_FORWARD", "order_id")])
p_tables = LP(request="SERVICE_TABLES", refresh_on=("ORDER_UPDATED", "PAYMENT_DONE"), columns=[
    ("table", "Bàn", 90), ("orders", "Số đơn chưa thanh toán", 160), ("status", "Trạng thái", 200), ("payment", "Thanh toán", 130)])
p_pay_check = LP(request="PAYMENT_STATUS_LIST", refresh_on=("ORDER_UPDATED", "PAYMENT_DONE"), columns=ORDER_COLS)
p_ready_log = LG(("ORDER_READY", "STAFF_CALLED"), "Thông báo món sẵn sàng và khách gọi nhân viên (phiên này)")
p_pay_inbox = LP(request="PAYMENT_PENDING", params={"only_requested": True}, refresh_on=("PAYMENT_REQUESTED", "PAYMENT_DONE"),
                 columns=ORDER_COLS, info=lambda pl: f"Đơn khách đã gửi yêu cầu thanh toán: {len(pl['rows'])}")
p_pending = LP(request="PAYMENT_PENDING", refresh_on=("PAYMENT_REQUESTED", "PAYMENT_DONE"), columns=ORDER_COLS,
               info=lambda pl: f"Tổng chờ thanh toán (công nợ): {int(pl['total_debt']):,} đ".replace(",", "."))
p_collect = LP(request="PAYMENT_PENDING", refresh_on=("PAYMENT_REQUESTED", "PAYMENT_DONE"), columns=ORDER_COLS, actions=[
    {"label": "Xác nhận đã thu tiền", "type": "PAYMENT_CONFIRM", "payload": lambda r: {"order_id": r["order_id"]},
     "ask": [("method", "Hình thức thanh toán", "choice", METHODS)], "confirm": "Xác nhận đã thu tiền đơn này?"}])
p_dash = LP(request="DASH_SUMMARY", columns=KV_COLS, auto_sec=10)
p_late = LP(request="LATE_LIST", auto_sec=10, refresh_on=("ALERT_LATE_ORDER",), columns=[
    ("order_id", "Đơn", 55), ("table", "Bàn", 70), ("name", "Món", 200), ("quantity", "SL", 40),
    ("status", "Trạng thái", 90), ("wait_min", "Chờ (phút)", 90)])
p_alert_log = LG(("ALERT_LATE_ORDER",), "Cảnh báo đơn trễ nhận được trong phiên này")
p_late_cfg = FP(fields=[("minutes", "Ngưỡng cảnh báo trễ (phút)", "text")], submit="LATE_CONFIG_SET", label="Lưu ngưỡng",
                success="Đã lưu. Áp dụng ngay, không cần khởi động lại.", reset=False)
p_top = LP(request="STATS_TOP_ITEMS", columns=[("name", "Món", 280), ("quantity", "Số lượng bán", 120)])
p_avg = LP(request="STATS_AVG_SERVICE", columns=KV_COLS)
p_shifts = LP(request="SHIFT_LIST", columns=SHIFT_COLS)
p_assign = LP(request="STAFF_BASIC", columns=[("id", "ID", 50), ("full_name", "Nhân viên", 220), ("role", "Vai trò", 110)],
              actions=[{"label": "Xếp ca cho nhân viên đã chọn", "type": "SHIFT_ASSIGN", "payload": lambda r: {"staff_id": r["id"]},
                        "ask": [("date", "Ngày (YYYY-MM-DD)", "text"), ("shift_name", "Ca", "choice", SHIFTS)]}])
p_shift_edit = LP(request="SHIFT_LIST", columns=SHIFT_COLS, actions=[
    {"label": "Đổi ca", "type": "SHIFT_UPDATE", "payload": lambda r: {"id": r["id"]},
     "ask": [("date", "Ngày (YYYY-MM-DD)", "text"), ("shift_name", "Ca", "choice", SHIFTS)],
     "defaults": {"date": "work_date", "shift_name": "shift_name"}},
    act("Xóa ca", "SHIFT_DELETE", "id", confirm="Xóa ca làm việc này?")])
p_staff = LP(request="STAFF_LIST", columns=STAFF_COLS)
p_staff_add = FP(fields=[("username", "Tên đăng nhập", "text"), ("full_name", "Họ tên", "text"),
                         ("password", "Mật khẩu (>= 6 ký tự)", "password"), ("role", "Vai trò", "choice", ROLES)],
                 submit="STAFF_ADD", label="Thêm tài khoản", success="Đã thêm tài khoản nhân viên.")
p_staff_lock = LP(request="STAFF_LIST", columns=STAFF_COLS, actions=[
    {"label": "Khóa", "type": "STAFF_LOCK", "payload": lambda r: {"id": r["id"], "locked": True},
     "confirm": "Khóa tài khoản này?"},
    {"label": "Mở khóa", "type": "STAFF_LOCK", "payload": lambda r: {"id": r["id"], "locked": False}},
    {"label": "Đổi vai trò", "type": "STAFF_SET_ROLE", "payload": lambda r: {"id": r["id"]},
     "ask": [("role", "Vai trò mới", "choice", ROLES)]}])
p_revenue = LP(request="REVENUE", choice=("period", [("Theo ngày", "day"), ("Theo tuần", "week"), ("Theo tháng", "month")]),
               columns=[("label", "Kỳ", 140), ("orders", "Số đơn", 80), ("revenue", "Doanh thu (đ)", 140, "money")],
               info=lambda pl: f"Tổng các kỳ hiển thị (gộp mọi ca): {int(pl['total']):,} đ".replace(",", "."))
p_overview = LP(request="OVERVIEW", columns=KV_COLS, auto_sec=10)

ALLM = (QL, PV, KB, KT)
MODULES = [
    ("PH01", "Quản trị hệ thống", [
        ("Giám sát phân hệ", A, [("Xem trạng thái phân hệ", p_status), ("Xem số client mỗi phân hệ", p_status)]),
        ("Quản lý kết nối", A, [("Xem danh sách session", p_sessions), ("Ngắt session treo", p_sessions)]),
        ("Cấu hình hệ thống", A, [("Cấu hình port và heartbeat", p_config), ("Cấu hình SSL/TLS", p_config)]),
        ("Quản lý dữ liệu", A, [("Kiểm tra kết nối CSDL", p_dbcheck), ("Sao lưu và phục hồi", p_backup)]),
        ("An ninh hệ thống", A, [("Khóa tài khoản/IP vi phạm", p_lock), ("Xem yêu cầu bị từ chối", p_rejected)])]),
    ("PH02", "Quản lý thực đơn", [
        ("Xem thực đơn", ALLM, [("Xem danh sách món", p_menu_view), ("Xem tình trạng còn/hết hàng", p_menu_view)]),
        ("Quản lý món", (QL,), [("Thêm món", FP(fields=MENU_FIELDS, submit="MENU_ADD", label="Thêm món",
                                                  success="Đã thêm món vào thực đơn.")),
                                ("Sửa món", p_menu_edit), ("Xóa món", p_menu_edit)]),
        ("Giá và tình trạng", (QL,), [("Cập nhật giá", p_menu_edit), ("Bật/tắt còn hàng", p_menu_edit)])]),
    ("PH03", "Đặt món & Đơn hàng", [
        ("Chọn món", (KB,), [("Chọn món và số lượng", p_order), ("Nhập ghi chú", p_order)]),
        ("Gửi yêu cầu", (KB,), [("Gửi yêu cầu chọn món cho phục vụ", p_order), ("Gọi nhân viên", p_call)]),
        ("Theo dõi đơn", (KB,), [("Xem trạng thái đơn", p_my_orders)])]),
    ("PH04", "Đặt bàn & Tài khoản khách", [
        ("Tài khoản khách", (KT,), [("Đăng ký", p_info_account), ("Đăng nhập", p_info_account)]),
        ("Đặt bàn", (KT,), [("Đặt bàn từ xa", p_res_form), ("Hủy đặt bàn", p_res_mine), ("Xem lịch sử đặt bàn", p_res_mine)]),
        ("Xử lý đặt bàn", (QL,), [("Xem danh sách đặt bàn", p_res_manage), ("Xác nhận đặt bàn", p_res_manage),
                                  ("Từ chối đặt bàn", p_res_manage)])]),
    ("PH05", "Pha chế (Bếp)", [
        ("Nhận đơn", (PC,), [("Nhận đơn từ phục vụ", p_kitchen), ("Xem danh sách đơn chờ", p_kitchen)]),
        ("Xử lý món", (PC,), [("Bắt đầu làm món", p_kitchen), ("Hoàn tất món", p_kitchen)]),
        ("Cảnh báo", (PC,), [("Nhận cảnh báo trễ", p_kitchen)])]),
    ("PH06", "Phục vụ", [
        ("Nhận và chuyển đơn", (PV,), [("Nhận yêu cầu chọn món của khách", p_svc_req), ("Chuyển đơn cho bếp", p_svc_req)]),
        ("Theo dõi món và bàn", (PV,), [("Nhận thông báo món sẵn sàng", p_ready_log), ("Xem trạng thái các bàn", p_tables)]),
        ("Kiểm tra thanh toán", (PV,), [("Kiểm tra trạng thái thanh toán", p_pay_check)])]),
    ("PH07", "Thanh toán & Công nợ", [
        ("Yêu cầu thanh toán", (KB, TN), [("Gửi yêu cầu thanh toán", p_pay_send), ("Nhận yêu cầu thanh toán", p_pay_inbox)]),
        ("Danh sách chờ (công nợ)", (TN, CQ), [("Xem danh sách chờ thanh toán", p_pending)]),
        ("Thu tiền", (TN,), [("Chọn hình thức thanh toán", p_collect), ("Xác nhận đã thu tiền", p_collect)])]),
    ("PH08", "Giám sát vận hành", [
        ("Theo dõi công việc", (QL,), [("Xem số đơn đang xử lý", p_dash), ("Xem đơn đang trễ", p_late)]),
        ("Cảnh báo trễ", (QL,), [("Nhận cảnh báo đơn trễ", p_alert_log), ("Cấu hình ngưỡng cảnh báo", p_late_cfg)])]),
    ("PH09", "Thống kê & Ca làm việc", [
        ("Thống kê vận hành", (QL,), [("Xem món bán chạy", p_top), ("Xem thời gian phục vụ trung bình", p_avg)]),
        ("Quản lý ca làm việc", (QL,), [("Xem lịch ca nhân viên", p_shifts), ("Xếp ca cho nhân viên", p_assign),
                                        ("Điều chỉnh ca", p_shift_edit)])]),
    ("PH10", "Nhân sự & Tài khoản", [
        ("Xem nhân sự", (CQ,), [("Xem danh sách nhân viên", p_staff)]),
        ("Quản lý tài khoản", (CQ,), [("Thêm tài khoản nhân viên", p_staff_add), ("Khóa tài khoản", p_staff_lock),
                                      ("Phân quyền vai trò", p_staff_lock)])]),
    ("PH11", "Điều hành chung (Chủ quán)", [
        ("Xem doanh thu", (CQ,), [("Xem doanh thu ngày/tuần/tháng", p_revenue), ("Gộp doanh thu nhiều ca", p_revenue)]),
        ("Xem điều hành chung", (CQ,), [("Xem tổng quan hoạt động quán", p_overview), ("Xem thống kê tổng hợp", p_top)])]),
]


def modules_for(role_key):
    """Danh sách (mã, tên, [(chức năng, [(con, factory)])]) mà vai trò này được thấy. Admin thấy tất cả."""
    out = []
    for code, name, funcs in MODULES:
        fl = [(fn, cons) for fn, roles, cons in funcs if role_key == "ADMIN" or role_key in roles]
        if fl:
            out.append((code, name, fl))
    return out



# Phụ trách: Nhi (View) - giao diện 11 phân hệ
