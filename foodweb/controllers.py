from builtins import print

from click import confirm
from flask import render_template, request, redirect, session, jsonify
from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.recaptcha import validators


from foodweb import app, dao, admin, login, utils, db
from flask_login import login_user, logout_user, login_required, current_user
from foodweb.models import Receipt, UserRole
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
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']
        if password.__eq__(confirm):
            try:
                # Đăng ký cơ bản không cần OTP, dùng username làm tên hiển thị
                dao.register(name=username,
                             username=username,
                             password=password)

                return redirect('/login')
            except:
                err_msg = 'Hệ thống đang có lỗi! Vui lòng quay lại sau!'
        else:
            err_msg = 'Mật khẩu KHÔNG khớp!'

    return render_template('register.html', err_msg=err_msg)



@annonymous_user
def login_my_user():
    form = ContactForm()
    err_msg = ""
    if request.method.__eq__('POST'):
        if request.form.get('g-recaptcha-response'):
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
            err_msg = "Vui lòng xác minh mình là con người!"

    return render_template('login.html', form=form, err_msg=err_msg)


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
    product_ids = dao.get_restaurant_menu_product_ids(restaurant_id)
    # Only show products explicitly mapped to this restaurant; do not fallback to all products
    products = dao.load_products_by_ids(product_ids)
    # Compute categories available for this restaurant to narrow header menu
    # Prefer explicit category mapping per restaurant if available
    cate_ids = dao.get_restaurant_category_ids(restaurant_id)
    categories_for_restaurant = dao.load_categories_by_ids(cate_ids) if cate_ids else dao.load_categories_by_product_ids(product_ids)
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
            pending_id = dao.add_pending_order(current_user.id, cart)
        except Exception as ex:
            print(str(ex))
            return jsonify({"status": 500})
        else:
            del session[key]
            session.pop('cart_restaurant_id', None)
            return jsonify({"status": 200, "pending_id": pending_id})

    return jsonify({"status": 200})


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
