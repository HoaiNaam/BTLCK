
from foodweb.models import Category, Product, User, Receipt, ReceiptDetails, Comment, PaymentMethod, Restaurant
from flask_login import current_user
from sqlalchemy import func
from foodweb import db
import hashlib
import json
import os
from datetime import datetime
 


def load_categories():
    return Category.query.all()


def load_products(cate_id=None, kw=None):
    query = Product.query.filter(Product.active.__eq__(True))

    if cate_id:
        query = query.filter(Product.category_id.__eq__(cate_id))

    if kw:
        query = query.filter(Product.name.contains(kw))

    return query.all()


def get_product_by_id(product_id):
    return Product.query.get(product_id)


def auth_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return User.query.filter(User.username.__eq__(username.strip()),
                             User.password.__eq__(password)).first()


def get_user_by_id(user_id):
    return User.query.get(user_id)

def get_user_by_username(username):
    return User.query.filter(User.username.__eq__(username.strip())).first()


def register(name, username, password, phonenumber=None, avatar=None):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    # Cung cấp giá trị mặc định nếu không truyền avatar
    default_avatar_url = avatar if (avatar is not None and str(avatar).strip() != "") else \
        "https://res.cloudinary.com/demo/image/upload/v1312461204/sample.jpg"

    u = User(name=name,
             username=username.strip(),
             password=password,
             image=default_avatar_url)
    db.session.add(u)
    db.session.commit()


def save_receipt(cart):
    if cart:
        r = Receipt(user=current_user)
        db.session.add(r)

        for c in cart.values():
            d = ReceiptDetails(quantity=c['quantity'], price=c['price'],
                               receipt=r, product_id=c['id'])
            db.session.add(d)

        db.session.commit()
        return r.id
    return None


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
def _read_json(file_name):
    file_path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return None


def _write_json(file_name, data):
    file_path = os.path.join(DATA_DIR, file_name)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_restaurants(kw=None):
    # Load từ database thay vì JSON
    query = Restaurant.query.filter(Restaurant.active == True)
    
    if kw:
        kw_norm = kw.strip().lower()
        query = query.filter(Restaurant.name.contains(kw_norm))
    
    # Sắp xếp theo ID giảm dần để Cơ Sở 3 (ID: 1) xuất hiện cuối cùng
    restaurants = query.order_by(Restaurant.id.desc()).all()
    
    # Convert database objects to dictionary format for compatibility
    result = []
    for r in restaurants:
        result.append({
            'id': r.id,
            'name': r.name,
            'address': r.address,
            'description': r.description or '',
            'image': r.image or '',
            'phone': r.phone or '',
            'email': r.email or ''
        })
    
    return result


def get_restaurant_by_id(restaurant_id):
    # Load từ database thay vì JSON
    restaurant = Restaurant.query.filter(Restaurant.id == int(restaurant_id), Restaurant.active == True).first()
    if restaurant:
        return {
            'id': restaurant.id,
            'name': restaurant.name,
            'address': restaurant.address,
            'description': restaurant.description or '',
            'image': restaurant.image or '',
            'phone': restaurant.phone or '',
            'email': restaurant.email or ''
        }
    return None


def load_products_by_ids(product_ids):
    if not product_ids:
        return []
    return Product.query.filter(Product.id.in_(product_ids), Product.active.__eq__(True)).all()


def load_categories_by_product_ids(product_ids):
    if not product_ids:
        return []
    return db.session.query(Category).join(Product, Product.category_id.__eq__(Category.id)) \
        .filter(Product.id.in_(product_ids), Product.active.__eq__(True)) \
        .distinct().all()


# -------------------- Restaurant <-> Categories mapping (JSON-based) --------------------
def get_restaurant_category_ids(restaurant_id):
    mapping = _read_json('restaurant_categories.json') or {}
    return mapping.get(str(restaurant_id), [])


def _set_restaurant_category_ids(restaurant_id, category_ids):
    mapping = _read_json('restaurant_categories.json') or {}
    mapping[str(restaurant_id)] = list({int(x) for x in category_ids})
    _write_json('restaurant_categories.json', mapping)
    return True


def add_category_to_restaurant(restaurant_id: int, category_id: int):
    ids = set(get_restaurant_category_ids(restaurant_id))
    ids.add(int(category_id))
    return _set_restaurant_category_ids(restaurant_id, list(ids))


def remove_category_from_restaurants(category_id: int):
    mapping = _read_json('restaurant_categories.json') or {}
    changed = False
    for k in list(mapping.keys()):
        vals = set(mapping.get(k, []))
        if int(category_id) in vals:
            vals.remove(int(category_id))
            mapping[k] = list(vals)
            changed = True
    if changed:
        _write_json('restaurant_categories.json', mapping)
    return True


def load_categories_by_ids(category_ids):
    if not category_ids:
        return []
    return Category.query.filter(Category.id.in_(category_ids)).all()


def get_restaurant_menu_product_ids(restaurant_id):
    mapping = _read_json('restaurant_products.json') or {}
    key = str(restaurant_id)
    return mapping.get(key, [])


def _set_restaurant_menu_product_ids(restaurant_id, product_ids):
    mapping = _read_json('restaurant_products.json') or {}
    mapping[str(restaurant_id)] = list(product_ids)
    _write_json('restaurant_products.json', mapping)
    return True


def add_product_to_restaurant_menu(restaurant_id: int, product_id: int):
    current = set(get_restaurant_menu_product_ids(restaurant_id))
    current.add(int(product_id))
    _set_restaurant_menu_product_ids(restaurant_id, list(current))
    return True


def remove_product_from_restaurant_menu(restaurant_id: int, product_id: int):
    current = set(get_restaurant_menu_product_ids(restaurant_id))
    if int(product_id) in current:
        current.remove(int(product_id))
        _set_restaurant_menu_product_ids(restaurant_id, list(current))
    return True



ORDER_STATUS_FILE = 'orders_status.json'
def get_order_status(receipt_id):
    data = _read_json(ORDER_STATUS_FILE) or {}
    return data.get(str(receipt_id), 'pending')


def update_order_status(receipt_id, status):
    data = _read_json(ORDER_STATUS_FILE) or {}
    data[str(receipt_id)] = status
    _write_json(ORDER_STATUS_FILE, data)
    return True



PENDING_ORDERS_FILE = 'pending_orders.json'
def add_pending_order(user_id, cart, payment_method=PaymentMethod.CASH):
    data = _read_json(PENDING_ORDERS_FILE) or {"seq": 0, "orders": {}}
    data["seq"] = int(data.get("seq", 0)) + 1
    pending_id = str(data["seq"])
    
    # Đảm bảo payment_method là PaymentMethod enum
    if isinstance(payment_method, PaymentMethod):
        payment_method_value = payment_method.value
    else:
        payment_method_value = int(payment_method)
    
    data["orders"][pending_id] = {
        "user_id": int(user_id),
        "cart": cart,
        "payment_method": payment_method_value,
        "created_at": datetime.now().isoformat()
    }
    _write_json(PENDING_ORDERS_FILE, data)
    return pending_id


def load_pending_orders():
    data = _read_json(PENDING_ORDERS_FILE) or {"orders": {}}
    orders_map = data.get("orders", {})
    # Normalize to list with id
    orders = []
    for k, v in orders_map.items():
        o = dict(v)
        o["id"] = k
        orders.append(o)
    # sort by id desc
    try:
        orders.sort(key=lambda x: int(x["id"]), reverse=True)
    except Exception:
        pass
    return orders


def get_pending_order(pending_id):
    data = _read_json(PENDING_ORDERS_FILE) or {"orders": {}}
    return data.get("orders", {}).get(str(pending_id))


def remove_pending_order(pending_id):
    data = _read_json(PENDING_ORDERS_FILE) or {"orders": {}}
    orders = data.get("orders", {})
    if str(pending_id) in orders:
        del orders[str(pending_id)]
        data["orders"] = orders
        _write_json(PENDING_ORDERS_FILE, data)
        return True
    return False


def save_receipt_for_user(cart, user_id, payment_method=PaymentMethod.CASH):
    if cart and user_id:
        r = Receipt(user_id=int(user_id), payment_method=payment_method)
        db.session.add(r)
        for c in cart.values():
            d = ReceiptDetails(quantity=int(c['quantity']), price=float(c['price']),
                               receipt=r, product_id=int(c['id']))
            db.session.add(d)
        db.session.commit()
        return r.id
    return None


# -------------------- Seed fast food items for restaurant 2 --------------------
def _get_or_create_category(name: str):
    cate = Category.query.filter(Category.name.__eq__(name)).first()
    if cate:
        return cate
    cate = Category(name=name)
    db.session.add(cate)
    db.session.commit()
    return cate


def ensure_fast_food_items_for_restaurant(restaurant_id: int = 2):

    fast_food_category = _get_or_create_category('Thức ăn nhanh')

    seed_items = [
        {"name": "Gà rán giòn", "price": 45000, "image": "https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998708/picture/Okinawa-Milk-Foam-Smoothie_hwvjjm.png"},
        {"name": "Khoai tây chiên", "price": 30000, "image": "https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996374/picture/Tra-Sua-Dao_hbdjf1.png"},
        {"name": "Hamburger bò", "price": 55000, "image": "https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996379/picture/Tr%C3%A0-s%E1%BB%AFa-Oolong-3J-2_to3ehm.png"},
        {"name": "Hamburger gà", "price": 52000, "image": "https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996374/picture/Tra-sua-tran-chau-HK_drv0pl.png"},
        {"name": "Xúc xích nướng", "price": 28000, "image": "https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996376/picture/Tr%C3%A0-s%E1%BB%AFa-Chocolate-2_lzbb7b.png"},
        {"name": "Bánh mì kẹp", "price": 35000, "image": "https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998722/picture/Tr%C3%A0-s%E1%BB%AFa-tr%C3%A0-%C4%91en-3_e2ue24.png"},
        {"name": "Pizza phô mai lát", "price": 69000, "image": "https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996379/picture/Tr%C3%A0-s%E1%BB%AFa-Oolong-2_du45i0.png"},
        {"name": "Bánh bao nhân thịt", "price": 25000, "image": "https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998707/picture/S%C6%B0%C6%A1ng-s%C3%A1o_ifx1pa.png"},
        {"name": "Hotdog", "price": 30000, "image": "https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998705/picture/kem-tc_jvc6xa.png"},
        {"name": "Cơm gà sốt", "price": 65000, "image": "https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998705/picture/Nha-%C4%90am_voubnn.png"},
    ]

    created_or_existing_ids = []
    for item in seed_items:
        prod = Product.query.filter(Product.name.__eq__(item["name"])) .first()
        if not prod:
            prod = Product(name=item["name"],
                           description=item["name"],
                           price=float(item["price"]),
                           image=item["image"],
                           category_id=fast_food_category.id)
            db.session.add(prod)
            db.session.commit()
        created_or_existing_ids.append(int(prod.id))

    # Overwrite mapping for this restaurant to ONLY fast food items
    _set_restaurant_menu_product_ids(restaurant_id, list(created_or_existing_ids))
    return list(created_or_existing_ids)

def count_product_by_cate():
    return db.session.query(Category.id, Category.name, func.count(Product.id))\
             .join(Product, Product.category_id.__eq__(Category.id), isouter=True)\
             .group_by(Category.id).all()


def stats_revenue(kw=None, from_date=None, to_date=None):
    query = db.session.query(Product.id, Product.name, func.sum(ReceiptDetails.price*ReceiptDetails.quantity))\
              .join(ReceiptDetails, ReceiptDetails.product_id.__eq__(Product.id))\
              .join(Receipt, ReceiptDetails.receipt_id.__eq__(Receipt.id))

    if kw:
        query = query.filter(Product.name.contains(kw))

    if from_date:
        query = query.filter(Receipt.created_date.__ge__(from_date))

    if to_date:
        query = query.filter(Receipt.created_date.__le__(to_date))

    return query.group_by(Product.id).order_by(-Product.id).all()


def load_comments(product_id):
    return Comment.query.filter(Comment.product_id.__eq__(product_id)).order_by(-Comment.id).all()


def save_comment(content, product_id):
    c = Comment(content=content, product_id=product_id, user=current_user)
    db.session.add(c)
    db.session.commit()

    return c





if __name__ == '__main__':
    from foodweb import app
    with app.app_context():
        pass






