from foodweb.models import Category, Product, Tag, User, Receipt, ReceiptDetails, UserRole
from foodweb import db, app, dao
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from wtforms import TextAreaField, FileField
from wtforms.validators import Optional
import cloudinary.uploader
from wtforms.widgets import TextArea
from flask import request, redirect, url_for, flash
from foodweb.models import Category

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
            # If upload fails, keep previous image value
            pass
        return super(ProductView, self).on_model_change(form, model, is_created)

    def after_model_change(self, form, model, is_created):
        """Route product to proper restaurant menu based on category.

        - If category name is 'Thức ăn nhanh' -> add to restaurant 2, remove from 1.
        - Else -> add to restaurant 1, remove from 2.
        """
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
    # Require selecting a restaurant branch when creating/updating a category
    form_extra_fields = {
        'restaurant_id': TextAreaField('Cơ sở (1 hoặc 2)')
    }

    def on_model_change(self, form, model, is_created):
        # Validate restaurant_id
        rid_val = None
        try:
            rid_val = int((form.restaurant_id.data or '').strip())
        except Exception:
            rid_val = None
        if rid_val not in (1, 2):
            raise ValueError('Phải chọn Cơ sở là 1 hoặc 2')

        # Map category to selected restaurant; remove from the other
        try:
            if rid_val == 1:
                dao.add_category_to_restaurant(1, int(model.id) if model.id else None)
                dao.remove_category_from_restaurants(int(model.id) if model.id else None)
                dao.add_category_to_restaurant(1, int(model.id))
            else:
                dao.add_category_to_restaurant(2, int(model.id) if model.id else None)
                dao.remove_category_from_restaurants(int(model.id) if model.id else None)
                dao.add_category_to_restaurant(2, int(model.id))
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
    column_list = ['id', 'created_date', 'user']
    column_labels = {
        'id': 'Mã HĐ',
        'created_date': 'Ngày tạo',
        'user': 'Khách hàng',
        'user_id': 'Mã KH',
        'details': 'Chi tiết'
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
        return self.render(
            'admin/orders_admin.html',
            receipts=receipts,
            statuses=statuses,
            pending_orders=pending_orders,
            pending_user_names=pending_user_names,
            total_receipts=total_receipts,
            confirmed_count=confirmed_count,
            pending_count=pending_count
        )

    @expose('/<int:receipt_id>/confirm')
    def confirm(self, receipt_id):
        dao.update_order_status(receipt_id, 'confirmed')
        return self.index()

    @expose('/pending/<pending_id>/confirm')
    def confirm_pending(self, pending_id):
        order = dao.get_pending_order(pending_id)
        if order:
            receipt_id = dao.save_receipt_for_user(order.get('cart'), order.get('user_id'))
            if receipt_id:
                dao.update_order_status(receipt_id, 'confirmed')
                dao.remove_pending_order(pending_id)
        return self.index()

admin = Admin(app=app, name='QUẢN TRỊ BÁN HÀNG', template_mode='bootstrap4', index_view=MyAdminView(), 
             base_template='admin/master.html')
admin.add_view(CategoryView(Category, db.session, name='Danh mục'))
# admin.add_view(TagView(Tag, db.session, name='Thẻ'))
admin.add_view(ProductView(Product, db.session, name='Sản phẩm'))
admin.add_view(UserView(User, db.session, name='Tài khoản'))
admin.add_view(ReceiptView(Receipt, db.session, name='Hóa đơn'))
admin.add_view(ReceiptDetailsView(ReceiptDetails, db.session, name='Chi tiết hóa đơn'))
admin.add_view(StatsView(name='Thống kê', endpoint='stats'))
admin.add_view(OrdersView(name='Đơn hàng', endpoint='orders'))
