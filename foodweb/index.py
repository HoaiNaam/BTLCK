from flask import render_template, request, redirect, session, jsonify
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from foodweb import app, dao, admin, login, utils, controllers
from flask_login import login_user, logout_user, login_required
from foodweb.decorators import annonymous_user
import cloudinary.uploader


app.add_url_rule('/', 'index', controllers.index)
app.add_url_rule('/products/<int:product_id>', 'product-detail', controllers.details)
app.add_url_rule('/login-admin', 'login-admin', controllers.login_admin, methods=['post'])
app.add_url_rule('/register', 'register', controllers.register, methods=['get', 'post'])
app.add_url_rule('/login', 'login-user', controllers.login_my_user, methods=['get', 'post'])
app.add_url_rule('/logout', 'logout', controllers.logout_my_user)
app.add_url_rule('/cart', 'cart', controllers.cart)
app.add_url_rule('/api/cart', 'add-cart', controllers.add_to_cart, methods=['post'])
app.add_url_rule('/api/cart/<product_id>', 'update-cart', controllers.update_cart, methods=['put'])
app.add_url_rule('/api/cart/<product_id>', 'delete-cart', controllers.delete_cart, methods=['delete'])
app.add_url_rule('/api/pay', 'pay', controllers.pay, methods=['post'])
app.add_url_rule('/api/pending/<pending_id>/cancel', 'cancel-pending', controllers.cancel_pending, methods=['post'])
app.add_url_rule('/api/products/<product_id>/comments', 'comment-list', controllers.comments)
app.add_url_rule('/api/products/<product_id>/comments', 'comment-add', controllers.add_comment, methods=['post'])

# Restaurants
app.add_url_rule('/restaurants', 'restaurants', controllers.restaurants_list)
app.add_url_rule('/restaurants/<int:restaurant_id>', 'restaurant-menu', controllers.restaurant_menu)

@app.context_processor
def common_attr():
    return {
        'categories': [],
        'cart': utils.cart_stats(session.get(app.config['CART_KEY']))
    }


@login.user_loader
def load_user(user_id):
    return dao.get_user_by_id(user_id)


if __name__ == "__main__":
    app.run(debug=True)