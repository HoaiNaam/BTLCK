from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text, Enum, DateTime
from sqlalchemy.orm import relationship, backref
from foodweb import db, app
from enum import Enum as UserEnum, unique
from flask_login import UserMixin
from datetime import datetime

 

import os

 


class UserRole(UserEnum):
    USER = 1
    ADMIN = 2

class PaymentMethod(UserEnum):
    CASH = 1
    BANK_TRANSFER = 2
    MOMO = 3
    ZALOPAY = 4
    VNPAY = 5


class BaseModel(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)


class Category(BaseModel):
    __tablename__ = 'category'

    name = Column(String(50), nullable=False)
    products = relationship('Product', backref='category', lazy=True)

    def __str__(self):
        return self.name


prod_tag = db.Table('prod_tag',
                    Column('product_id', Integer, ForeignKey('product.id'), primary_key=True),
                    Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True))


class Product(BaseModel):
    name = Column(String(50), nullable=False)
    description = Column(Text)
    price = Column(Float, default=0)
    image = Column(String(500))
    active = Column(Boolean, default=True)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    receipt_details = relationship('ReceiptDetails', backref='product', lazy=True)
    tags = relationship('Tag', secondary='prod_tag', lazy='subquery',
                        backref=backref('products', lazy=True))
    comments = relationship('Comment', backref='product', lazy=True)

    def __str__(self):
        return self.name


class Tag(BaseModel):
    name = Column(String(50), nullable=False, unique=True)

    def __str__(self):
        return self.name


class User(BaseModel, UserMixin):
    name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    image = Column(String(500), nullable=False)
    active = Column(Boolean, default=True)
    user_role = Column(Enum(UserRole), default=UserRole.USER)
    receipts = relationship('Receipt', backref='user', lazy=True)
    comments = relationship('Comment', backref='user', lazy=True)

    def __str__(self):
        return self.name


class Receipt(BaseModel):
    created_date = Column(DateTime, default=datetime.now())
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.CASH)
    details = relationship('ReceiptDetails', backref='receipt', lazy=True)

    def __str__(self):
        try:
            return f"Hóa đơn #{self.id}"
        except Exception:
            return "Hóa đơn"


class ReceiptDetails(BaseModel):
    quantity = Column(Integer, default=0)
    price = Column(Float, default=0)
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)


class Comment(BaseModel):
    content = Column(String(255), nullable=False)
    created_date = Column(DateTime, default=datetime.now())
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    product_id = Column(Integer, ForeignKey(Product.id), nullable=False)

    def __str__(self):
        return self.content


class Restaurant(BaseModel):
    __tablename__ = 'restaurant'
    
    name = Column(String(100), nullable=False)
    address = Column(String(200), nullable=False)
    description = Column(Text)
    image = Column(String(500))
    phone = Column(String(20))
    email = Column(String(100))
    active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.now())
    
    def __str__(self):
        return self.name


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        import hashlib

        password = str(hashlib.md5('123456'.encode('utf-8')).hexdigest())
        u = User(name='Hoài Nam', username='admin', password=password,
                 user_role=UserRole.ADMIN,
                 image='https://res.cloudinary.com/dhwuwy0to/image/upload/v1678329949/Vinh_2_nybzzs.jpg')

        u1 = User(name='Hoài Nam 1', username='admin1', password=password,
                 user_role=UserRole.USER,
                 image='https://res.cloudinary.com/dhwuwy0to/image/upload/v1678329949/Vinh_2_nybzzs.jpg')

        u2 = User(name='Hoài Nam 2', username='admin2', password=password,
                 user_role=UserRole.USER,
                 image='https://res.cloudinary.com/dhwuwy0to/image/upload/v1678329949/Vinh_2_nybzzs.jpg')
        db.session.add_all([u, u1, u2])
        db.session.commit()
        c1 = Category(name='Trà trái cây')
        c2 = Category(name='Trà sữa')
        c3 = Category(name='Topping')

        db.session.add_all([c1, c2, c3])
        db.session.commit()

        p1 = Product(name="Okinawa Oreo Cream Milk Tea", price="30000", description="Thơm ngon bổ dưỡng",
                     image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998708/picture/Okinawa-Oreo-Cream-Milk-Tea_xtswyp.png",
                     category_id=1)

        p2 = Product(name="Okinawa Milk Foam Smoothie", price="35000", description="Thơm ngon bổ dưỡng",
                     image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998708/picture/Okinawa-Milk-Foam-Smoothie_hwvjjm.png",
                     category_id=1)

        p3 = Product(name="Trà sữa Okinawa", price="30000", description="Thơm ngon bổ dưỡng",
                     image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998701/picture/Hinh-Web-OKINAWA-TR%C3%80-S%E1%BB%AEA_s83wh6.png",
                     category_id=1)

        p4 = Product(name="Sữa Tươi Okinawa", price="30000", description="Thơm ngon bổ dưỡng",
                     image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998708/picture/Okinawa-Oreo-Cream-Milk-Tea_xtswyp.png",
                     category_id=1)

        p5 = Product(name="Okinawa Latte", price="30000", description="Thơm ngon bổ dưỡng",
                     image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998708/picture/Okinawa-Milk-Foam-Smoothie_hwvjjm.png",
                     category_id=1)

        p6 = Product(name="Strawberry Milk Tea", price="30000", description="Thơm ngon bổ dưỡng",
                     image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996374/picture/Tra-Xanh-Sua-Dau_nbprij.png",
                     category_id=1)

        p7 = Product(name="Strawberry Cookie Milk Tea", price="30000", description="Thơm ngon bổ dưỡng",
                     image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996374/picture/Tra-Sua-Dau-Cookie-1_kxilfi.png",
                     category_id=1)

        p8 = Product(name="Mint Choco Milk Teaa", price="30000", description="Thơm ngon bổ dưỡng",
                     image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996366/picture/Mint-Chocolate-Milk-Tea-w-Pearl-Iced_gvgmv7.png",
                     category_id=1)

        p9 = Product(name="Trà Sữa Trân Châu Hoàng Kim", price="30000", description="Thơm ngon bổ dưỡng",
                     image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996374/picture/Tra-sua-tran-chau-HK_drv0pl.png",
                     category_id=1)

        p10 = Product(name="Trà Sữa Đào", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996377/picture/Tra-Sua-Dao_hbdjf1.png",
                      category_id=2)

        p11 = Product(name="Trà Sữa Xoài Trân Châu Đen", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996369/picture/Mango-Milktea_kofita.png",
                      category_id=2)

        p12 = Product(name="Trà sữa Oolong 3J", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996379/picture/Tr%C3%A0-s%E1%BB%AFa-Oolong-3J-2_to3ehm.png",
                      category_id=1)

        p13 = Product(name="Trà Sữa Pudding Đậu Đỏ", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996381/picture/Tr%C3%A0-s%E1%BB%AFa-Pudding-%C4%91%E1%BA%ADu-%C4%91%E1%BB%8F-2_ygwdwt.png",
                      category_id=1)

        p14 = Product(name="Trà Sữa Chocolate", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998716/picture/Tr%C3%A0-s%E1%BB%AFa-Chocolate-2_lzbb7b.png",
                      category_id=1)

        p15 = Product(name="Trà Sữa Trân Châu Đen", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998722/picture/Tr%C3%A0-s%E1%BB%AFa-Tr%C3%A2n-ch%C3%A2u-%C4%91en-1_lsr9yc.png",
                      category_id=1)

        p16 = Product(name="Trà Sữa Hokkaido", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998722/picture/Tr%C3%A0-s%E1%BB%AFa-tr%C3%A0-%C4%91en-3_e2ue24.png",
                      category_id=1)

        p17 = Product(name="Trà Sữa Sương Sáo", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996380/picture/Tr%C3%A0-s%E1%BB%AFa-s%C6%B0%C6%A1ng-s%C3%A1o_emalbk.png",
                      category_id=1)

        p18 = Product(name="Trà Sữa Oolong", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996379/picture/Tr%C3%A0-s%E1%BB%AFa-Oolong-2_du45i0.png",
                      category_id=1)

        p19 = Product(name="Trà Sữa Trà Đen", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996377/picture/Tr%C3%A0-s%E1%BB%AFa-Hokkaido-2_hcs72s.png",
                      category_id=1)

        p20 = Product(name="Trà Sữa Khoai Môn", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996377/picture/Tr%C3%A0-s%E1%BB%AFa-Khoai-m%C3%B4n-2_bexzkt.png",
                      category_id=2)

        p21 = Product(name="ALISAN Trái Cây", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998697/picture/ALISAN-TRA%CC%81I-CA%CC%82Y_lczuwv.png",
                      category_id=2)

        p22 = Product(name="Đào hồng mận hột é", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677996369/picture/Hinh-Web-OKINAWA-TR%C3%80-S%E1%BB%AEA_yqn5et.png",
                      category_id=2)

        p23 = Product(name="Combo 3 Loại Hạt", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998696/picture/Combo-3-lo%E1%BA%A1i-h%E1%BA%A1t_e1gphk.png",
                      category_id=3)

        p24 = Product(name="Kem Sữa", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998700/picture/Kem-S%E1%BB%AFa_dyabg1.png",
                      category_id=3)

        p25 = Product(name="Nha Đam", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998705/picture/Nha-%C4%90am_voubnn.png",
                      category_id=3)

        p26 = Product(name="Sương sáo", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998707/picture/S%C6%B0%C6%A1ng-s%C3%A1o_ifx1pa.png",
                      category_id=3)

        p27 = Product(name="Kem Trân Châu", price="30000", description="Thơm ngon bổ dưỡng",
                      image="https://res.cloudinary.com/dhwuwy0to/image/upload/v1677998705/picture/kem-tc_jvc6xa.png",
                      category_id=3)

        db.session.add_all([p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16, p17, p18, p19, p20, p21, p22, p23, p24, p25, p26, p27])
        db.session.commit()