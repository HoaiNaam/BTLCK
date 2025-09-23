# Hướng dẫn cài đặt và chạy dự án FlaskFoodWeb (Windows)

Dự án là một ứng dụng web đặt món ăn viết bằng Flask + SQLAlchemy, kèm reCAPTCHA v2 và tài nguyên tĩnh.

## 1) Yêu cầu môi trường
- Python 3.10+
- MySQL/MariaDB (có tài khoản và quyền tạo CSDL)
- Git (tùy chọn)

## 2) Tải mã nguồn
Nếu đã có thư mục dự án, có thể bỏ qua.
```powershell
# Ví dụ
git clone <repo-url> FlaskFoodWeb
cd FlaskFoodWeb
```

## 3) Tạo và kích hoạt môi trường ảo
```powershell
python -m venv .venv
. .venv\Scripts\Activate.ps1
```
Nếu PowerShell chặn script:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 4) Cài thư viện
```powershell
pip install -r requirements.txt
```

## 5) Cấu hình kết nối CSDL và reCAPTCHA
Mở `QLNH/foodweb/__init__.py` và chỉnh:

- Kết nối MySQL:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://<user>:<password>@localhost/foodappdb?charset=utf8mb4'
```
Đổi `<user>`/`<password>` theo máy bạn.

- reCAPTCHA v2:
```python
SITE_KEY_V2 = "<SITE_KEY_V2>"
SECRET_KEY_V2 = "<SECRET_KEY_V2>"
app.config['RECAPTCHA_PUBLIC_KEY'] = SITE_KEY_V2
app.config['RECAPTCHA_PRIVATE_KEY'] = SECRET_KEY_V2
```
(Lấy key tại trang quản trị reCAPTCHA “classic” của Google.)

- Cloudinary (nếu dùng upload):
```python
cloudinary.config(cloud_name='...', api_key='...', api_secret='...')
```

## 6) Chuẩn bị CSDL
Tạo CSDL rỗng:
```sql
CREATE DATABASE foodappdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
Khởi tạo bảng (tùy chọn, nếu cần từ models):
```powershell
python
>>> from QLNH.foodweb import db
>>> from QLNH.foodweb import models
>>> db.create_all()
>>> exit()
```
Dữ liệu mẫu JSON nằm tại `QLNH/foodweb/data/`.

## 7) Chạy ứng dụng
Cách 1 (khuyến nghị):
```powershell
python QLNH\foodweb\index.py
```
Cách 2 (nếu PYTHONPATH phù hợp):
```powershell
python -m QLNH.foodweb.index
```
Mặc định chạy tại `http://127.0.0.1:5000`.

## 8) Các đường dẫn chính
- `/` Trang chủ
- `/register` Đăng ký
- `/login` Đăng nhập
- `/cart` Giỏ hàng
- `/restaurants`, `/restaurants/<restaurant_id>`
- API giỏ hàng: `/api/cart` (POST), `/api/cart/<product_id>` (PUT/DELETE)
- `/api/pay` Thanh toán

## 9) Ghi chú về reCAPTCHA
- Dự án dùng reCAPTCHA v2 Checkbox cho đăng ký/đăng nhập.
- Không thể ép luôn hiện thử thách; Google tự đánh giá rủi ro. Có thể tăng “Security preference” trong trang quản trị.

## 10) Lỗi thường gặp
- Không kết nối DB: kiểm tra `SQLALCHEMY_DATABASE_URI`, dịch vụ MySQL, quyền user, tồn tại DB.
- Lỗi import: chạy lệnh từ thư mục gốc `FlaskFoodWeb`, ưu tiên `python QLNH\foodweb\index.py`.
- Tài nguyên tĩnh không cập nhật: nhấn Ctrl + F5 để refresh cứng.

## 11) Cấu trúc thư mục (rút gọn)
```
FlaskFoodWeb/
  QLNH/
    foodweb/
      __init__.py
      index.py
      controllers.py
      dao.py
      models.py
      templates/
      static/
      data/
```

## 12) Gợi ý triển khai
- Dùng `waitress`/`gunicorn`/`uWSGI` phía sau Nginx/Apache.
- Đặt secret (DB, reCAPTCHA, Cloudinary) qua biến môi trường khi đưa lên production.

Nếu gặp lỗi, vui lòng gửi log để mình hỗ trợ thêm.
