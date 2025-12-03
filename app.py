from flask import Flask, render_template, request, redirect, url_for, flash
from config import Config
from models import db, Product, Supplier, Stock, Operation
from datetime import datetime
import redis

redis_client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

app = Flask(__name__)
app.config.from_object(Config)

# Do not initialize the database at import time so tests can configure it.
# The DB will be initialized when running the app directly or by tests via
# `models.db.init_app(test_app)`.

# ---------------- Главная ----------------


@app.route("/")
def index():
    cache_key = "dashboard_stats"
    cached = redis_client.get(cache_key)

    if cached:
        # Если есть в кеше - возвращаем из Redis
        import json
        data = json.loads(cached)
        return render_template("index.html",
                               total_products=data['products'],
                               total_suppliers=data['suppliers'],
                               low_count=data['low_stock'])

    total_products = Product.query.count()
    total_suppliers = Supplier.query.count()
    low = Stock.query.filter(Stock.quantity <= Stock.min_stock).count()
    
    # Сохраняем в кеш на 30 секунд
    import json
    data = {
        'products': total_products,
        'suppliers': total_suppliers, 
        'low_stock': low
    }
    redis_client.setex(cache_key, 30, json.dumps(data))  
    
    return render_template("index.html",
                           total_products=total_products,
                           total_suppliers=total_suppliers,
                           low_count=low)


# ---------------- Список товаров ----------------
@app.route("/products")
def products():
    q = request.args.get("q", "")
    category = request.args.get("category", "")
    supplier = request.args.get("supplier", "")

    query = Product.query

    if q:
        query = query.filter(
            (Product.name.contains(q)) |
            (Product.sku.contains(q))
        )

    if category:
        query = query.filter(Product.category.contains(category))

    if supplier:
        try:
            sid = int(supplier)
            query = query.filter(Product.supplier_id == sid)
        except:
            pass

    items = query.all()
    return render_template("product_list.html", products=items)


# ---------------- Добавление товара ----------------
@app.route("/product/add", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        p = Product(
            name=request.form["name"],
            sku=request.form["sku"],
            category=request.form.get("category"),
            unit=request.form.get("unit"),
            description=request.form.get("description"),
            supplier_id=request.form.get("supplier") or None
        )
        db.session.add(p)
        db.session.commit()

        stock = Stock(product_id=p.id, quantity=0, min_stock=0)
        db.session.add(stock)
        db.session.commit()

        flash("Товар добавлен", "success")
        return redirect(url_for("products"))

    suppliers = Supplier.query.all()
    return render_template("add_product.html", suppliers=suppliers)


# ---------------- Поставщики ----------------
@app.route("/suppliers")
def suppliers():
    return render_template("suppliers_list.html", suppliers=Supplier.query.all())


@app.route("/supplier/add", methods=["POST", "GET"])
def add_supplier():
    if request.method == "POST":
        s = Supplier(name=request.form["name"], contact=request.form.get("contact"))
        db.session.add(s)
        db.session.commit()
        flash("Поставщик добавлен", "success")
        return redirect(url_for("suppliers"))

    return render_template("add_supplier.html")


# ---------------- Операции ----------------
@app.route("/operations")
def operations():
    df = request.args.get("from", "")
    dt = request.args.get("to", "")

    query = Operation.query

    if df:
        try:
            d1 = datetime.strptime(df, "%Y-%m-%d")
            query = query.filter(Operation.date >= d1)
        except:
            pass

    if dt:
        try:
            d2 = datetime.strptime(dt, "%Y-%m-%d")
            query = query.filter(Operation.date <= d2)
        except:
            pass

    ops = query.order_by(Operation.date.desc()).all()
    return render_template("operations_list.html", operations=ops)


@app.route("/operations/add", methods=["GET", "POST"])
def add_operation_view():
    if request.method == "POST":
        pid = int(request.form["product_id"])
        op_type = request.form["type"]
        qty = int(request.form["quantity"])

        op = Operation(
            product_id=pid,
            type=op_type,
            quantity=qty,
            date=datetime.strptime(request.form["date"], "%Y-%m-%d"),
            from_wh=request.form.get("from_wh"),
            to_wh=request.form.get("to_wh"),
            responsible=request.form.get("responsible"),
            note=request.form.get("note")
        )

        db.session.add(op)

        stock = Stock.query.filter_by(product_id=pid).first()

        if op_type == "in":
            stock.quantity += qty
        elif op_type == "out":
            stock.quantity -= qty
        elif op_type == "adjust":
            stock.quantity -= qty

        db.session.commit()

        flash("Операция добавлена", "success")
        return redirect(url_for("operations"))

    return render_template("add_operation.html",
                           products=Product.query.all())


# ---------------- Минимальные остатки ----------------
@app.route("/stock/low")
def stock_low():
    items = Stock.query.filter(Stock.quantity <= Stock.min_stock).all()
    return render_template("stock_low.html", stocks=items)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
