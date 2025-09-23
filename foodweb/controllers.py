from builtins import print

from click import confirm
from flask import render_template, request, redirect, session, jsonify, flash
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.recaptcha import validators
from werkzeug.utils import secure_filename
import os
import uuid
import requests
from datetime import datetime, timedelta

from foodweb import app, dao, admin, login, utils, db
from flask_login import login_user, logout_user, login_required, current_user
from foodweb.models import Receipt, UserRole, PaymentMethod, Category
from foodweb.decorators import annonymous_user
import cloudinary.uploader
from werkzeug.utils import redirect


def index():
    cate_id = request.args.get('category_id')
    kw = request.args.get('keyword')
    products = dao.load_products(cate_id, kw)

    return render_template('index.html', products=products)


def details(product_id):
    p = dao.get_product_by_id(product_id)
    return render_template('details.html', product=p)


def login_admin():
    username = request.form['username']
    password = request.form['password']

    user = dao.auth_user(username=username, password=password)
    if user:
        login_user(user=user)

    return redirect('/admin')


 

 


def register():
    err_msg = ''
    if request.method.__eq__('POST'):
        # Kiểm tra reCAPTCHA response
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not recaptcha_response:
            err_msg = "Vui lòng hoàn thành thử thách reCAPTCHA!"
            return render_template('register.html', err_msg=err_msg)
        
        # Verify reCAPTCHA với Google
        secret_key = app.config['RECAPTCHA_PRIVATE_KEY']
        verify_url = 'https://www.google.com/recaptcha/api/siteverify'
        verify_data = {
            'secret': secret_key,
            'response': recaptcha_response,
            'remoteip': request.remote_addr
        }
        
        try:
            verify_response = requests.post(verify_url, data=verify_data)
            verify_result = verify_response.json()
            
            if not verify_result.get('success'):
                err_msg = "reCAPTCHA không hợp lệ! Vui lòng thử lại."
                return render_template('register.html', err_msg=err_msg)
        except Exception as e:
            print(f"Lỗi verify reCAPTCHA: {str(e)}")
            err_msg = "Lỗi xác minh reCAPTCHA! Vui lòng thử lại."
            return render_template('register.html', err_msg=err_msg)
        
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']
        name = request.form.get('name', username)  # Lấy tên từ form, mặc định là username
        
        if password.__eq__(confirm):
            try:
                # Kiểm tra user đã tồn tại chưa
                existing_user = dao.get_user_by_username(username)
                if existing_user:
                    err_msg = 'Tên đăng nhập đã tồn tại!'
                    return render_template('register.html', err_msg=err_msg)
                
                # Xử lý upload ảnh avatar
                avatar_url = None
                if 'avatar' in request.files:
                    file = request.files['avatar']
                    if file and file.filename != '':
                        try:
                            # Kiểm tra định dạng file
                            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
                            if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                                # Tạo tên file unique và ngắn gọn
                                file_extension = file.filename.rsplit('.', 1)[1].lower()
                                unique_filename = f"{uuid.uuid4().hex[:8]}.{file_extension}"
                                
                                # Lưu file vào thư mục uploads/avatars
                                upload_folder = os.path.join(app.root_path, 'static', 'uploads', 'avatars')
                                os.makedirs(upload_folder, exist_ok=True)
                                file_path = os.path.join(upload_folder, unique_filename)
                                file.save(file_path)
                                
                                # Tạo URL để truy cập ảnh
                                avatar_url = f"/static/uploads/avatars/{unique_filename}"
                            else:
                                err_msg = 'Định dạng file không được hỗ trợ! Chỉ chấp nhận: PNG, JPG, JPEG, GIF, WEBP'
                                return render_template('register.html', err_msg=err_msg)
                        except Exception as upload_error:
                            print(f"Lỗi upload ảnh: {str(upload_error)}")
                            # Nếu upload lỗi, vẫn cho phép đăng ký nhưng không có avatar
                            avatar_url = None
                
                # Đăng ký user với avatar
                dao.register(name=name,
                             username=username,
                             password=password,
                             avatar=avatar_url)

                # Xóa các thông báo cũ (nếu có) để chỉ hiện 1 thông báo mới
                try:
                    session.pop('_flashes', None)
                except Exception:
                    pass

                flash('Bạn đã đăng ký tài khoản thành công! Mời đăng nhập để đặt món ăn.', 'success')
                return redirect('/login')
            except Exception as e:
                print(f"Lỗi đăng ký: {str(e)}")
                import traceback
                traceback.print_exc()
                err_msg = 'Hệ thống đang có lỗi! Vui lòng quay lại sau!'
        else:
            err_msg = 'Mật khẩu KHÔNG khớp!'

    return render_template('register.html', err_msg=err_msg)



@annonymous_user
def login_my_user():
    err_msg = ""
    if request.method.__eq__('POST'):
        # Kiểm tra reCAPTCHA response
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not recaptcha_response:
            err_msg = "Vui lòng hoàn thành thử thách reCAPTCHA!"
        else:
            # Verify reCAPTCHA với Google
            secret_key = app.config['RECAPTCHA_PRIVATE_KEY']
            verify_url = 'https://www.google.com/recaptcha/api/siteverify'
            verify_data = {
                'secret': secret_key,
                'response': recaptcha_response,
                'remoteip': request.remote_addr
            }
            
            try:
                verify_response = requests.post(verify_url, data=verify_data)
                verify_result = verify_response.json()
                
                if verify_result.get('success'):
                    username = request.form['username']
                    password = request.form['password']

                    user = dao.auth_user(username=username, password=password)
                    if user:
                        login_user(user=user)
                        n = request.args.get("next")
                        return redirect(n if n else '/')
                    else:
                        err_msg = "Sai tài khoản hoặc mật khẩu!"
                else:
                    err_msg = "reCAPTCHA không hợp lệ! Vui lòng thử lại."
            except Exception as e:
                print(f"Lỗi verify reCAPTCHA: {str(e)}")
                err_msg = "Lỗi xác minh reCAPTCHA! Vui lòng thử lại."

    return render_template('login.html', err_msg=err_msg)


def logout_my_user():
    logout_user()
    return redirect('/login')


def cart():
    form = ContactForm()
    # session['cart'] = {
    #     "1": {
    #         "id": "1",
    #         "name": "iPhone 13",
    #         "price": 13000,
    #         "quantity": 2
    #     },
    #     "2": {
    #         "id": "2",
    #         "name": "iPhone 14",
    #         "price": 13000,
    #         "quantity": 2
    #     }
    # }

    return render_template('cart.html', form=form)


def add_to_cart():
    key = app.config['CART_KEY']
    cart = session[key] if key in session else {}

    data = request.json
    id = str(data['id'])
    restaurant_id = data.get('restaurant_id')

    # Enforce single-restaurant cart if restaurant_id provided
    cart_restaurant_key = 'cart_restaurant_id'
    current_cart_restaurant_id = session.get(cart_restaurant_key)
    if restaurant_id:
        if current_cart_restaurant_id and str(current_cart_restaurant_id) != str(restaurant_id):
            cart = {}
        session[cart_restaurant_key] = restaurant_id

    if id in cart:
        cart[id]['quantity'] += 1
    else:
        name = data['name']
        price = data['price']

        cart[id] = {
            "id": id,
            "name": name,
            "price": price,
            "quantity": 1
        }

    session[key] = cart

    return jsonify(utils.cart_stats(cart))


def restaurants_list():
    kw = request.args.get('kw')
    restaurants = dao.load_restaurants(kw)
    return render_template('restaurants.html', restaurants=restaurants, kw=kw)


def restaurant_menu(restaurant_id):
    restaurant = dao.get_restaurant_by_id(restaurant_id)
    if not restaurant:
        return redirect('/restaurants')
    # Ensure fast food items exist for restaurant 2
    try:
        if int(restaurant_id) == 2:
            dao.ensure_fast_food_items_for_restaurant(2)
    except Exception as ex:
        print(str(ex))
    # Compute categories for this restaurant strictly by DB relation
    try:
        cate_ids = [int(c.id) for c in Category.query.filter(Category.restaurant_id == int(restaurant_id)).all()]
    except Exception:
        cate_ids = []
    categories_for_restaurant = dao.load_categories_by_ids(cate_ids)
    # Load products that belong to these categories
    products = dao.load_products_by_category_ids(cate_ids)
    return render_template('restaurant_menu.html', restaurant=restaurant, products=products, categories=categories_for_restaurant)


def admin_orders():
    if not current_user.is_authenticated or current_user.user_role != UserRole.ADMIN:
        return redirect('/')
    # List receipts with status
    receipts = db.session.query(Receipt).order_by(-Receipt.id).all()
    statuses = {r.id: dao.get_order_status(r.id) for r in receipts}
    return render_template('admin/orders.html', receipts=receipts, statuses=statuses)


def admin_confirm_order(receipt_id):
    if not current_user.is_authenticated or current_user.user_role != UserRole.ADMIN:
        return redirect('/')
    try:
        dao.update_order_status(receipt_id, 'confirmed')
    except Exception as ex:
        print(str(ex))
    return redirect('/admin/orders')


def update_cart(product_id):
    key = app.config['CART_KEY']
    cart = session.get(key)

    if cart and product_id in cart:
        cart[product_id]['quantity'] = int(request.json['quantity'])

    session[key] = cart

    return jsonify(utils.cart_stats(cart))


def delete_cart(product_id):
    key = app.config['CART_KEY']
    cart = session.get(key)

    if cart and product_id in cart:
        del cart[product_id]

    session[key] = cart
    if not cart or len(cart.keys()) == 0:
        session.pop('cart_restaurant_id', None)

    return jsonify(utils.cart_stats(cart))


@login_required
def pay():
    key = app.config['CART_KEY']
    cart = session.get(key)

    if cart:
        try:
            # Lấy phương thức thanh toán từ request
            payment_method_id = request.json.get('payment_method', 1)  # Mặc định là tiền mặt
            payment_method = PaymentMethod(int(payment_method_id))
            
            pending_id = dao.add_pending_order(current_user.id, cart, payment_method)
        except Exception as ex:
            print(f"Error in pay(): {str(ex)}")
            return jsonify({"status": 500, "error": str(ex)})
        else:
            del session[key]
            session.pop('cart_restaurant_id', None)
            return jsonify({"status": 200, "pending_id": pending_id})

    return jsonify({"status": 200})


@login_required
def cancel_pending(pending_id):
    try:
        order = dao.get_pending_order(pending_id)
        if not order:
            return jsonify({"status": 404, "message": "Đơn không tồn tại"})

        # Chỉ chủ đơn mới được hủy
        if int(order.get("user_id")) != int(current_user.id):
            return jsonify({"status": 403, "message": "Không có quyền hủy đơn này"})

        # Kiểm tra thời gian tạo đơn <= 60 giây
        created_at_str = order.get("created_at")
        try:
            created_at = datetime.fromisoformat(created_at_str)
        except Exception:
            created_at = datetime.now() - timedelta(minutes=5)
        if (datetime.now() - created_at).total_seconds() > 60:
            return jsonify({"status": 410, "message": "Hết thời gian hủy đơn (quá 60 giây)"})

        # Không ghi nhận hóa đơn khi khách hàng hủy trong thời gian cho phép
        # Cập nhật trạng thái pending thành canceled để admin còn thấy ở màn hình Đơn hàng
        dao.cancel_pending_order(pending_id)
        return jsonify({"status": 200, "pending_id": pending_id, "state": "canceled"})
    except Exception as ex:
        return jsonify({"status": 500, "message": str(ex)})


def comments(product_id):
    data = []
    for c in dao.load_comments(product_id=product_id):
        data.append({
            'id': c.id,
            'content': c.content,
            'created_date': str(c.created_date),
            'user': {
                'name': c.user.name,
                'avatar': c.user.image
            }
        })

    return jsonify(data)


def add_comment(product_id):
    try:
        c = dao.save_comment(product_id=product_id, content=request.json['content'])
    except:
        return jsonify({'status': 500})

    return jsonify({
        'status': 204,
        'comment': {
            'id': c.id,
            'content': c.content,
            'created_date': str(c.created_date),
            'user': {
                'name': c.user.name,
                'avatar': c.user.image
            }
        }
    })

class ContactForm(FlaskForm):
    recaptcha = RecaptchaField(validators=[validators.Recaptcha(message='Invalid reCAPTCHA.')])


if __name__ == '__main__':
    from foodweb import app

    with app.app_context():
        pass
