from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Supplier(db.Model): # type: ignore
    __tablename__ = "suppliers"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.Text)

    products = db.relationship("Product", backref="supplier")

class Supplier2(db.Model): # type: ignore
    __tablename__ = "suppliers2"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.Text)




class Product(db.Model): # type: ignore
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sku = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100))
    unit = db.Column(db.String(20))
    description = db.Column(db.Text)

    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"))

    stock = db.relationship("Stock", uselist=False, backref="product")
    operations = db.relationship("Operation", backref="product")


class Stock(db.Model): # type: ignore
    __tablename__ = "stocks"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    quantity = db.Column(db.Integer, default=0)
    min_stock = db.Column(db.Integer, default=0)
    warehouse = db.Column(db.String(100), default="Основной")


class Operation(db.Model): # type: ignore
    __tablename__ = "operations"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))
    type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    date = db.Column(db.DateTime, default=datetime.utcnow)

    from_wh = db.Column(db.String(100))
    to_wh = db.Column(db.String(100))
    responsible = db.Column(db.String(100))
    note = db.Column(db.Text)
