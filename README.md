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
