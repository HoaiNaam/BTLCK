from foodweb.models import Category, Product, Tag, User, Receipt, ReceiptDetails, UserRole, Restaurant, PaymentMethod
from foodweb import db, app, dao
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from wtforms import TextAreaField, FileField, SelectField
from wtforms.validators import Optional
import cloudinary.uploader
from wtforms.widgets import TextArea
from flask import request, redirect, url_for, flash
from foodweb.models import Category
from datetime import datetime, timedelta

class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

class CKTextAreaWidget(TextArea):
    def __call__(self, field, **kwargs):
        if kwargs.get('class'):
            kwargs['class'] += ' ckeditor'
        else:
            kwargs.setdefault('class', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(TextAreaField):
    widget = CKTextAreaWidget()


class ProductView(ModelView):
    column_searchable_list = ['name', 'description']
    column_filters = ['name', 'price']
    can_view_details = True
    can_export = True
    column_exclude_list = ['image', 'receipt_details']
    column_labels = {
        'id': 'Mã',
        'name': 'Tên sản phẩm',
        'description': 'Mô tả',
        'price': 'Giá',
        'image': 'Ảnh',
        'active': 'Kích hoạt',
        'category': 'Danh mục',
        'category_id': 'Mã danh mục',
        'tags': 'Thẻ',
        'comments': 'Bình luận'
    }
    extra_js = ['//cdn.ckeditor.com/4.6.0/standard/ckeditor.js']
    form_overrides = {
        'description': CKTextAreaField
    }
    # Hide raw image url field from the form; we will use file upload field instead
    form_excluded_columns = ('image', 'comments', 'tags', 'receipt_details')
    # Add a file upload control for product image
    form_extra_fields = {
        'image_file': FileField('Ảnh sản phẩm (tải từ máy)', validators=[Optional()])
    }

    def is_accessible(self):
        return current_user.is_authenticated

    def on_model_change(self, form, model, is_created):
        """Upload selected image to Cloudinary and store its URL into model.image."""
        try:
            image_storage = getattr(form, 'image_file', None)
            if image_storage and image_storage.data:
                upload_result = cloudinary.uploader.upload(image_storage.data, folder='foodapp/products')
                if upload_result and upload_result.get('secure_url'):
                    model.image = upload_result['secure_url']
        except Exception:
            pass
        return super(ProductView, self).on_model_change(form, model, is_created)

    def after_model_change(self, form, model, is_created):
        try:
            cate = None
            # model.category may be available if relationship is loaded
            if getattr(model, 'category', None):
                cate = model.category
            else:
                if getattr(model, 'category_id', None):
                    cate = db.session.get(Category, int(model.category_id))
            cate_name = (cate.name if cate else '').strip().lower()
            is_fast_food = (cate_name == 'thức ăn nhanh')

            if is_fast_food:
                dao.add_product_to_restaurant_menu(2, int(model.id))
                dao.remove_product_from_restaurant_menu(1, int(model.id))
            else:
                dao.add_product_to_restaurant_menu(1, int(model.id))
                dao.remove_product_from_restaurant_menu(2, int(model.id))
        except Exception:
            pass
        return super(ProductView, self).after_model_change(form, model, is_created)

    def on_model_delete(self, model):
        """Cleanup related data before deletion (do not block here)."""
        try:
            # Remove from restaurant menus
            try:
                dao.remove_product_from_restaurant_menu(1, int(model.id))
                dao.remove_product_from_restaurant_menu(2, int(model.id))
            except Exception:
                pass
            # Remove comments
            if hasattr(model, 'comments') and model.comments:
                for c in list(model.comments):
                    db.session.delete(c)
            # Clear tag associations
            if hasattr(model, 'tags') and model.tags:
                model.tags = []
        except Exception:
            pass

    def delete_model(self, model):
        """Gracefully prevent deletion when product has receipts to avoid error page."""
        if hasattr(model, 'receipt_details') and (len(model.receipt_details) > 0):
            # Soft-delete: keep order history, hide product from use
            try:
                model.active = False
                # optional cleanup of menus so không còn bán
                try:
                    dao.remove_product_from_restaurant_menu(1, int(model.id))
                    dao.remove_product_from_restaurant_menu(2, int(model.id))
                except Exception:
                    pass
                db.session.add(model)
                db.session.commit()
                flash('Sản phẩm đã được vô hiệu hóa để giữ nguyên lịch sử đơn hàng.', 'info')
                return True
            except Exception:
                flash('Không thể vô hiệu hóa sản phẩm.', 'danger')
                return False
        # Proactively cleanup relationships before calling super delete
        try:
            try:
                dao.remove_product_from_restaurant_menu(1, int(model.id))
                dao.remove_product_from_restaurant_menu(2, int(model.id))
            except Exception:
                pass
            if hasattr(model, 'comments') and model.comments:
                for c in list(model.comments):
                    db.session.delete(c)
            if hasattr(model, 'tags') and model.tags:
                model.tags = []
            db.session.flush()
        except Exception:
            pass
        return super(ProductView, self).delete_model(model)


class CategoryView(AuthenticatedModelView):
    column_labels = {
        'id': 'Mã',
        'name': 'Tên danh mục',
        'products': 'Sản phẩm'
    }
    column_searchable_list = ['name']
    # Hide product and auto relationship field 'restaurant' from the create/edit form
    form_excluded_columns = ('products', 'restaurant')
    # Require selecting a restaurant branch when creating/updating a category
    # Dynamically populated in create_form/edit_form
    form_extra_fields = {
        'restaurant_id': SelectField('Cơ sở', choices=[], coerce=int)
    }

    def _populate_restaurant_choices(self, form):
        try:
            choices = [(int(r.id), f"{r.name or 'Cơ sở'}") for r in db.session.query(Restaurant).filter(Restaurant.active == True).order_by(Restaurant.id.asc()).all()]
            if not choices:
                choices = [(1, 'Cơ sở 1')]
            form.restaurant_id.choices = choices
        except Exception:
            form.restaurant_id.choices = [(1, 'Cơ sở 1')]
        return form

    def create_form(self):
        form = super(CategoryView, self).create_form()
        return self._populate_restaurant_choices(form)

    def edit_form(self, obj=None):
        form = super(CategoryView, self).edit_form(obj)
        return self._populate_restaurant_choices(form)

    def on_model_change(self, form, model, is_created):
        # Validate selected restaurant exists
        rid_val = None
        try:
            rid_val = int(form.restaurant_id.data)
        except Exception:
            rid_val = None
        # Ensure restaurant exists
        if not rid_val or not db.session.get(Restaurant, rid_val):
            raise ValueError('Cơ sở không tồn tại')

        # Persist relation to DB
        try:
            model.restaurant_id = int(rid_val)
        except Exception:
            pass
        return super(CategoryView, self).on_model_change(form, model, is_created)


class TagView(AuthenticatedModelView):
    column_labels = {
        'id': 'Mã',
        'name': 'Tên thẻ'
    }
    column_searchable_list = ['name']


class UserView(AuthenticatedModelView):
    column_exclude_list = ['password']
    column_labels = {
        'id': 'Mã',
        'name': 'Họ tên',
        'username': 'Tên đăng nhập',
        'password': 'Mật khẩu',
        'image': 'Ảnh đại diện',
        'active': 'Kích hoạt',
        'user_role': 'Vai trò',
        'receipts': 'Hóa đơn',
        'comments': 'Bình luận'
    }


class ReceiptView(AuthenticatedModelView):
    column_list = ['id', 'created_date', 'user', 'payment_method']
    column_labels = {
        'id': 'Mã HĐ',
        'created_date': 'Ngày tạo',
        'user': 'Khách hàng',
        'user_id': 'Mã KH',
        'payment_method': 'Phương thức thanh toán',
        'details': 'Chi tiết'
    }

    
    def _payment_method_formatter(self, context, model, name):
        """Custom formatter for payment method column"""
        from markupsafe import Markup
        if model.payment_method:
            payment_method = model.payment_method
            if payment_method.value == 1:
                return Markup('<span class="badge bg-success"><i class="fas fa-money-bill-wave"></i> Tiền mặt</span>')
            elif payment_method.value == 2:
                return Markup('<span class="badge bg-primary"><i class="fas fa-university"></i> Chuyển khoản</span>')
            elif payment_method.value == 3:
                return Markup('<span class="badge bg-warning"><i class="fas fa-mobile-alt"></i> MoMo</span>')
            elif payment_method.value == 4:
                return Markup('<span class="badge bg-info"><i class="fas fa-credit-card"></i> ZaloPay</span>')
            elif payment_method.value == 5:
                return Markup('<span class="badge bg-secondary"><i class="fas fa-credit-card"></i> VNPay</span>')
            else:
                return Markup('<span class="badge bg-light text-dark">Không xác định</span>')
        return Markup('<span class="badge bg-light text-dark">Không xác định</span>')
    
    column_formatters = {
        'payment_method': _payment_method_formatter
    }


class ReceiptDetailsView(AuthenticatedModelView):
    column_list = ['id', 'receipt', 'product', 'quantity', 'price']
    column_labels = {
        'id': 'Mã',
        'receipt': 'Hóa đơn',
        'product': 'Sản phẩm',
        'quantity': 'Số lượng',
        'price': 'Đơn giá',
        'receipt_id': 'Mã HĐ',
        'product_id': 'Mã SP'
    }

class StatsView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

    @expose('/')
    def index(self):
        try:
            stats = dao.stats_revenue(kw=request.args.get('kw'),
                                      from_date=request.args.get('from_date'),
                                      to_date=request.args.get('to_date'))
            return self.render('admin/stats.html', stats=stats)
        except Exception as e:
            # Fallback nếu có lỗi
            return self.render('admin/stats.html', stats=[])

    def get_url(self, endpoint, **kwargs):
        if endpoint == 'admin.stats':
            return '/admin/stats/'
        return super(StatsView, self).get_url(endpoint, **kwargs)


class MyAdminView(AdminIndexView):
    @expose('/')
    def index(self):
        stats = dao.count_product_by_cate()
        return self.render('admin/index.html', stats=stats)

    def get_url(self, endpoint, **kwargs):
        if endpoint == 'admin.index':
            return '/admin/'
        return super(MyAdminView, self).get_url(endpoint, **kwargs)

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect(url_for('admin.login_view'))
        return super(MyAdminView, self)._handle_view(name, **kwargs)


class OrdersView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

    @expose('/')
    def index(self):
        receipts = db.session.query(Receipt).order_by(-Receipt.id).all()
        statuses = {r.id: dao.get_order_status(r.id) for r in receipts}
        pending_orders = dao.load_pending_orders()

        # Auto-accept pending orders older than 60 seconds
        try:
            now = datetime.utcnow()
            to_confirm = []
            for o in list(pending_orders):
                try:
                    created_at = datetime.fromisoformat(o.get('created_at'))
                except Exception:
                    created_at = now - timedelta(minutes=5)
                # Bỏ qua đơn đã hủy (vẫn hiển thị ở bảng pending như canceled)
                if str(o.get('status')) == 'canceled':
                    continue
                if (now - created_at).total_seconds() > 60:
                    to_confirm.append(o)
            for o in to_confirm:
                rid = dao.save_receipt_for_user(o.get('cart'), o.get('user_id'), PaymentMethod(o.get('payment_method', 1)))
                if rid:
                    dao.update_order_status(rid, 'confirmed')
                    dao.remove_pending_order(o.get('id'))
            if to_confirm:
                # reload lists after changes
                receipts = db.session.query(Receipt).order_by(-Receipt.id).all()
                statuses = {r.id: dao.get_order_status(r.id) for r in receipts}
                pending_orders = dao.load_pending_orders()
        except Exception:
            pass
        # Separate canceled pending orders from active pending orders
        canceled_pending_orders = [o for o in pending_orders if str(o.get('status')) == 'canceled']
        pending_orders = [o for o in pending_orders if str(o.get('status')) != 'canceled']
        # Build a map of user_id -> name for pending orders
        user_ids = list({int(o.get('user_id')) for o in pending_orders if o.get('user_id') is not None})
        pending_user_names = {}
        if user_ids:
            for uid, name in db.session.query(User.id, User.name).filter(User.id.in_(user_ids)).all():
                pending_user_names[str(uid)] = name
        # Summary metrics
        total_receipts = len(receipts)
        confirmed_count = sum(1 for r in receipts if statuses.get(r.id) == 'confirmed')
        pending_count = len(pending_orders)
        canceled_count = len(canceled_pending_orders) + sum(1 for r in receipts if statuses.get(r.id) == 'canceled')
        return self.render(
            'admin/orders_admin.html',
            receipts=receipts,
            statuses=statuses,
            pending_orders=pending_orders,
            canceled_pending_orders=canceled_pending_orders,
            pending_user_names=pending_user_names,
            total_receipts=total_receipts,
            confirmed_count=confirmed_count,
            pending_count=pending_count,
            canceled_count=canceled_count
        )

    @expose('/<int:receipt_id>/confirm')
    def confirm(self, receipt_id):
        dao.update_order_status(receipt_id, 'confirmed')
        return self.index()

    @expose('/pending/<pending_id>/confirm')
    def confirm_pending(self, pending_id):
        order = dao.get_pending_order(pending_id)
        if order:
            # Lấy phương thức thanh toán từ pending order
            payment_method_id = order.get('payment_method', 1)
            payment_method = PaymentMethod(payment_method_id)
            
            receipt_id = dao.save_receipt_for_user(order.get('cart'), order.get('user_id'), payment_method)
            if receipt_id:
                dao.update_order_status(receipt_id, 'confirmed')
                dao.remove_pending_order(pending_id)
        return self.index()

class RestaurantView(AuthenticatedModelView):
    column_list = ['id', 'name', 'address', 'phone', 'email', 'active', 'created_date']
    column_searchable_list = ['name', 'address', 'phone', 'email']
    column_filters = ['active', 'created_date']
    can_view_details = True
    can_export = True
    can_create = True
    can_edit = True
    can_delete = True
    column_exclude_list = ['image', 'description']
    column_labels = {
        'id': 'Mã',
        'name': 'Tên cơ sở',
        'address': 'Địa chỉ',
        'description': 'Mô tả',
        'image': 'Ảnh',
        'phone': 'Số điện thoại',
        'email': 'Email',
        'active': 'Kích hoạt',
        'created_date': 'Ngày tạo'
    }
    
    # Hide relationship 'categories' and image path from the form; we'll use upload field
    form_excluded_columns = ('image', 'created_date', 'categories')
    form_extra_fields = {
        'image_file': FileField('Ảnh cơ sở (tải từ máy)', validators=[Optional()])
    }
    
    # Custom form labels
    form_labels = {
        'name': 'Tên cơ sở',
        'address': 'Địa chỉ',
        'description': 'Mô tả',
        'phone': 'Số điện thoại',
        'email': 'Email',
        'active': 'Kích hoạt'
    }
    
    # Form validation
    form_args = {
        'name': {
            'validators': [Optional()],
            'description': 'Nhập tên cơ sở (ví dụ: IMPROOK - Cơ sở 1)'
        },
        'address': {
            'validators': [Optional()],
            'description': 'Nhập địa chỉ đầy đủ của cơ sở'
        },
        'phone': {
            'validators': [Optional()],
            'description': 'Nhập số điện thoại liên hệ'
        },
        'email': {
            'validators': [Optional()],
            'description': 'Nhập email liên hệ'
        }
    }

    def on_model_change(self, form, model, is_created):
        """Upload selected image to Cloudinary and store its URL into model.image."""
        try:
            image_storage = getattr(form, 'image_file', None)
            if image_storage and image_storage.data:
                upload_result = cloudinary.uploader.upload(image_storage.data, folder='foodapp/restaurants')
                if upload_result and upload_result.get('secure_url'):
                    model.image = upload_result['secure_url']
        except Exception:
            # If upload fails, keep previous image value
            pass
        return super(RestaurantView, self).on_model_change(form, model, is_created)
    
    def on_model_delete(self, model):
        """Cleanup related data before deletion."""
        try:
            # Add any cleanup logic here if needed
            pass
        except Exception:
            pass
        return super(RestaurantView, self).on_model_delete(model)
    
    def get_url(self, endpoint, **kwargs):
        """Ensure proper URL generation for restaurant views."""
        if endpoint == 'restaurant.index':
            return '/admin/restaurant/'
        return super(RestaurantView, self).get_url(endpoint, **kwargs)


admin = Admin(app=app, name='QUẢN TRỊ BÁN HÀNG', template_mode='bootstrap4', index_view=MyAdminView(), 
             base_template='admin/master.html')
admin.add_view(CategoryView(Category, db.session, name='Danh mục'))
admin.add_view(ProductView(Product, db.session, name='Sản phẩm'))
admin.add_view(RestaurantView(Restaurant, db.session, name='Cơ sở'))
admin.add_view(UserView(User, db.session, name='Tài khoản'))
admin.add_view(ReceiptView(Receipt, db.session, name='Hóa đơn'))
admin.add_view(ReceiptDetailsView(ReceiptDetails, db.session, name='Chi tiết hóa đơn'))
admin.add_view(StatsView(name='Thống kê', endpoint='stats'))
admin.add_view(OrdersView(name='Đơn hàng', endpoint='orders'))
