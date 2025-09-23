import json
import pytest


# Fixture tạo test client của Flask
@pytest.fixture(scope='module')
def app_client():
    # Đảm bảo thêm thư mục QLNH (chứa package foodweb) vào sys.path
    import os, sys
    pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if pkg_root not in sys.path:
        sys.path.insert(0, pkg_root)

    # Import ứng dụng và đăng ký route
    from foodweb import app  # khởi tạo trong foodweb/__init__.py
    # Đảm bảo các route được load
    import foodweb.index  # noqa: F401

    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False

    with app.test_client() as client:
        yield client


def test_login_page_get_200(app_client):
    # Trang đăng nhập phải truy cập được (GET 200)
    resp = app_client.get('/login')
    assert resp.status_code == 200


def test_register_page_get_200(app_client):
    # Trang đăng ký phải truy cập được (GET 200)
    resp = app_client.get('/register')
    assert resp.status_code == 200


def test_cart_add_update_delete_flow(app_client):
    # Thêm sản phẩm vào giỏ
    payload = {
        'id': 1,
        'name': 'Test Product',
        'price': 10000,
        'restaurant_id': 1
    }
    resp = app_client.post('/api/cart', data=json.dumps(payload), content_type='application/json')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total_quantity'] == 1
    assert data['total_amount'] == 10000

    # Cập nhật số lượng
    resp = app_client.put('/api/cart/1', data=json.dumps({'quantity': 3}), content_type='application/json')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total_quantity'] == 3
    assert data['total_amount'] == 30000

    # Xóa sản phẩm
    resp = app_client.delete('/api/cart/1')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['total_quantity'] == 0
    assert data['total_amount'] == 0


def test_cart_single_restaurant_enforced(app_client):
    # Thêm sản phẩm từ cơ sở 1
    payload1 = {'id': 1, 'name': 'P1', 'price': 10000, 'restaurant_id': 1}
    _ = app_client.post('/api/cart', data=json.dumps(payload1), content_type='application/json')

    # Thêm sản phẩm từ cơ sở 2 phải reset giỏ hàng
    payload2 = {'id': 2, 'name': 'P2', 'price': 5000, 'restaurant_id': 2}
    resp = app_client.post('/api/cart', data=json.dumps(payload2), content_type='application/json')
    assert resp.status_code == 200
    data = resp.get_json()
    # Chỉ còn sản phẩm vừa thêm
    assert data['total_quantity'] == 1
    assert data['total_amount'] == 5000

    # Dọn dẹp giỏ hàng
    _ = app_client.delete('/api/cart/2')


def test_comments_list_empty_with_monkeypatch(app_client, monkeypatch):
    # Monkeypatch DAO để không truy cập DB thật, trả về danh sách rỗng
    from foodweb import dao

    def fake_load_comments(product_id):
        return []

    monkeypatch.setattr(dao, 'load_comments', fake_load_comments)
    resp = app_client.get('/api/products/999/comments')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert data == []


def test_pay_requires_login_redirect(app_client):
    # API thanh toán phải yêu cầu đăng nhập: chưa login sẽ bị chuyển hướng
    resp = app_client.post('/api/pay', data=json.dumps({}), content_type='application/json', follow_redirects=False)
    # Flask-Login trả 302 redirect về trang /login (hoặc 401 tùy cấu hình)
    assert resp.status_code in (302, 401)
    # Ở chế độ test mặc định, 302 sẽ có Location tới /login?next=...
    if resp.status_code == 302:
        assert '/login' in resp.headers.get('Location', '')


