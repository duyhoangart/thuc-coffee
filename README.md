# Thức Coffee

Hệ thống quản lý quán cà phê theo mô hình Client-Server (LAN + Internet), viết bằng Python Socket (TCP).

## 1. Công nghệ

| Hạng mục | Lựa chọn |
| --- | --- |
| Ngôn ngữ | Python 3.10 trở lên |
| Giao tiếp mạng | `socket`, `threading`, `ssl` (cổng Internet bọc SSL/TLS) |
| Giao thức | Message JSON tự thiết kế (`type`, `payload`) |
| Cơ sở dữ liệu | SQLite (`sqlite3`, tệp cục bộ trên máy server) |
| Giao diện | Tkinter |
| Quản lý mã nguồn | Git + GitHub (repo công khai) |

Dự án chỉ dùng thư viện chuẩn, không cần `pip install` để chạy ứng dụng.

## 2. Cài đặt môi trường (mỗi thành viên làm một lần)

1. Cài **Python 3.10+** từ python.org. Trên Windows nhớ tick **Add Python to PATH** và để mục **tcl/tk** được chọn.
2. Cài **Git** từ git-scm.com.
3. (Khuyến nghị) Cài **VS Code** và **DB Browser for SQLite** để xem tệp `.db`.
4. Clone và kiểm tra:

```bash
git clone https://github.com/<tai-khoan>/thuc-coffee.git
cd thuc-coffee
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux
python scripts/check_env.py
```

Tất cả dòng báo `[OK ]` là môi trường sẵn sàng. Nếu dòng Tkinter báo lỗi, cài lại Python và chọn mục tcl/tk (Windows), hoặc `sudo apt install python3-tk` (Ubuntu).

5. Tạo cấu hình cục bộ: sao chép `config/config.example.json` thành `config/config.json` và sửa nếu cần.

## 3. Cấu trúc thư mục

```
thuc-coffee/
├── server/      # Xử lý kết nối, xác thực, phân quyền, handler theo phân hệ
├── client/      # Giao diện Tkinter, màn hình theo vai trò
├── protocol/    # Định nghĩa message JSON, mã lỗi, hàm gửi/nhận
├── database/    # Kết nối SQLite, schema, hàm truy vấn
├── config/      # config.example.json (config.json không đưa lên Git)
├── scripts/     # check_env.py và các script hỗ trợ
├── tests/       # Kiểm thử
├── docs/        # Báo cáo, sơ đồ, slide
├── data/        # Tệp .db cục bộ (không đưa lên Git)
└── certs/       # Chứng chỉ SSL cục bộ (không đưa lên Git)
```

## 4. Quy trình làm việc với Git

- Nhánh `main`: luôn chạy được. Không commit trực tiếp vào `main`.
- Mỗi người làm trên nhánh riêng, đặt tên `ten/chuc-nang`, ví dụ `an/ph02-thucdon`.
- Commit nhỏ, thông điệp rõ: `PH02: thêm chức năng thêm món`.
- Xong việc thì mở Pull Request, một bạn khác xem rồi mới gộp.
- Trước khi làm: `git pull origin main`.

```bash
git checkout -b ten/chuc-nang
git add .
git commit -m "PHxx: mô tả ngắn"
git push -u origin ten/chuc-nang
```

## 5. Lưu ý an toàn vì repo công khai

Không đưa lên GitHub: mật khẩu, tệp `.db` có dữ liệu thật, khóa/chứng chỉ SSL (`*.key`, `*.pem`), `config/config.json`. Các mục này đã nằm trong `.gitignore`. Nếu lỡ commit thì báo cả nhóm để xử lý, không chỉ xóa file vì lịch sử Git vẫn còn.

## 6. Chạy ứng dụng

Tại thư mục gốc dự án (sau khi đã làm bước 2):

```bash
copy config\config.example.json config\config.json   # chỉ làm lần đầu (macOS/Linux: cp)
python run_server.py          # terminal 1: chạy server (tự tạo data/thuccoffee.db và dữ liệu mẫu)
python run_client.py          # terminal 2: mở app, có thể mở nhiều cửa sổ để thử nhiều vai trò
```

Nếu client chạy trên máy khác trong LAN, sửa `server_address` trong `config/config.json` (hoặc nhập địa chỉ ở màn hình đăng nhập).

**Tài khoản mẫu (chỉ để chạy thử, đổi mật khẩu khi dùng thật):**

| Vai trò | Tên đăng nhập | Mật khẩu |
| --- | --- | --- |
| Admin | `admin` | `admin123` |
| Chủ quán | `chuquan` | `chuquan123` |
| Quản lý | `quanly` | `quanly123` |
| Thu ngân | `thungan` | `thungan123` |
| Phục vụ | `phucvu` | `phucvu123` |
| Pha chế | `phache` | `phache123` |

Khách tại quán: tab "Khách tại quán", chọn số bàn (không cần tài khoản). Khách đặt bàn từ xa: tab "Khách đặt bàn từ xa", bấm Đăng ký rồi đăng nhập.

**Thử workflow 1 (đặt món):** mở 5 cửa sổ client: Khách bàn 1, Phục vụ, Pha chế, Thu ngân, Quản lý.
Khách chọn món và gửi yêu cầu → Phục vụ chọn "Chuyển đơn cho bếp" → Pha chế bấm "Bắt đầu làm món", "Hoàn tất món" → Phục vụ nhận thông báo món sẵn sàng → Khách gửi yêu cầu thanh toán → Thu ngân "Xác nhận đã thu tiền" (chọn hình thức).

**Thử workflow 2 (đặt bàn):** Khách đặt bàn từ xa đăng ký, đăng nhập, đặt bàn (giờ dạng `2026-12-01 18:30`) → Quản lý vào PH04 "Xử lý đặt bàn", chọn Xác nhận hoặc Từ chối → Khách xem kết quả, có thể hủy.

## 7. Kiểm thử tự động

```bash
python -m unittest tests.test_workflow -v        # server: 2 workflow, phân quyền, cảnh báo trễ, đặt bàn, Admin
xvfb-run -a python tests/gui_smoke.py            # Linux: mở thử mọi chức năng con của mọi vai trò (cần xvfb)
```

## 8. SSL/TLS cho cổng Internet (tùy chọn khi thử, cần khi triển khai)

Tạo chứng chỉ tự ký (cần OpenSSL):

```bash
openssl req -x509 -newkey rsa:2048 -nodes -keyout certs/server.key -out certs/server.crt -days 365 -subj "/CN=thuccoffee"
```

Server tự bật SSL cho cổng Internet khi có `certs/server.crt` và `certs/server.key`. Khi đó đặt `"internet_ssl": true` trong `config/config.json` của client. Nếu không có chứng chỉ, server cảnh báo và chạy không mã hóa (chỉ dùng để thử).

## 9. Phân hệ và mã nguồn

| Phân hệ | Server (`server/handlers/`) | Client |
| --- | --- | --- |
| PH01 Quản trị hệ thống | `ph01_quantri.py`, `common.py` | `client/modules.py` |
| PH02 Quản lý thực đơn | `ph02_thucdon.py` | `client/modules.py` |
| PH03 Đặt món & Đơn hàng | `ph03_donhang.py` | `client/order_panel.py` |
| PH04 Đặt bàn & Tài khoản khách | `ph04_datban.py` | `client/modules.py` |
| PH05 Pha chế (Bếp) | `ph05_phache.py` | `client/modules.py` |
| PH06 Phục vụ | `ph06_phucvu.py` | `client/modules.py` |
| PH07 Thanh toán & Công nợ | `ph07_thanhtoan.py` | `client/modules.py` |
| PH08 Giám sát vận hành | `ph08_giamsat.py` | `client/modules.py` |
| PH09 Thống kê & Ca làm việc | `ph09_thongke.py` | `client/modules.py` |
| PH10 Nhân sự & Tài khoản | `ph10_nhansu.py` | `client/modules.py` |
| PH11 Điều hành chung (Chủ quán) | `ph11_dieuhanh.py` | `client/modules.py` |

Thêm một chức năng mới: viết hàm `@handler("TÊN_MESSAGE", "PHxx", roles)` trong file handler của phân hệ, rồi thêm một dòng panel trong `client/modules.py`.
