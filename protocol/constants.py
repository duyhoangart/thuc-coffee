"""Hằng số dùng chung cho server và client."""

# Vai trò
ADMIN, QUANLY, CHUQUAN = "ADMIN", "QUANLY", "CHUQUAN"
THUNGAN, PHUCVU, PHACHE, KHACH = "THUNGAN", "PHUCVU", "PHACHE", "KHACH"
STAFF_ROLES = (ADMIN, QUANLY, CHUQUAN, THUNGAN, PHUCVU, PHACHE)
ASSIGNABLE_ROLES = (QUANLY, THUNGAN, PHUCVU, PHACHE)  # Chủ quán được cấp

# Trạng thái đơn
ORDER_WAIT_SERVICE = "Chờ phục vụ"
ORDER_WAIT_KITCHEN = "Chờ bếp"
ORDER_COOKING = "Đang làm"
ORDER_READY = "Sẵn sàng"
# Trạng thái món
ITEM_WAIT, ITEM_DOING, ITEM_DONE = "Chờ", "Đang làm", "Xong"
# Thanh toán
PAY_UNPAID, PAY_PAID = "Chưa thanh toán", "Đã thanh toán"
PAY_METHODS = ("Tiền mặt", "Chuyển khoản", "QR")
# Đặt bàn
RES_PENDING, RES_OK, RES_NO, RES_CANCEL = "Chờ xác nhận", "Đã xác nhận", "Từ chối", "Đã hủy"
# Ca làm việc
SHIFT_NAMES = ("Sáng", "Chiều", "Tối")

# Tên phân hệ (dùng cho màn hình Admin)
MODULE_NAMES = {
    "PH01": "Quản trị hệ thống", "PH02": "Quản lý thực đơn",
    "PH03": "Đặt món & Đơn hàng", "PH04": "Đặt bàn & Tài khoản khách",
    "PH05": "Pha chế (Bếp)", "PH06": "Phục vụ", "PH07": "Thanh toán & Công nợ",
    "PH08": "Giám sát vận hành", "PH09": "Thống kê & Ca làm việc",
    "PH10": "Nhân sự & Tài khoản", "PH11": "Điều hành chung (Chủ quán)",
}
# Vai trò nào thuộc phân hệ nào (để đếm client đang online)
MODULE_ROLES = {
    "PH01": (ADMIN,), "PH02": (QUANLY, KHACH, PHUCVU), "PH03": (KHACH,),
    "PH04": (KHACH, QUANLY), "PH05": (PHACHE,), "PH06": (PHUCVU,),
    "PH07": (THUNGAN, CHUQUAN, KHACH), "PH08": (QUANLY,), "PH09": (QUANLY,),
    "PH10": (CHUQUAN,), "PH11": (CHUQUAN,),
}
