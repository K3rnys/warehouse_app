# -*- coding: utf-8 -*-
"""
Складец — Flask-приложение с in-memory заглушкой вместо PostgreSQL.
Реализует: учёт товаров, операции (приход/расход/списание/перемещение),
поиск/фильтрацию, список поставок по дате, минимальные остатки, добавление записей.
"""
from flask import Flask, render_template, request, redirect, url_for, flash
from wtforms import Form, StringField, SelectField, IntegerField, TextAreaField, DateField, validators
from datetime import datetime
import copy

app = Flask(__name__)
app.secret_key = "dev-secret-key"

# ---------------- In-memory DB (заглушка) ----------------
DB = {
    "products": {},     # id -> {id, name, sku, category, unit, supplier_id, description}
    "suppliers": {},    # id -> {id, name, contact}
    "stocks": {},       # product_id -> {product_id, quantity, min_stock, warehouse}
    "operations": [],   # list of {id, product_id, type, quantity, date, from_wh, to_wh, responsible, note}
}
_NEXT = {"product": 1, "supplier": 1, "operation": 1}

def _next_id(kind):
    nid = _NEXT[kind]
    _NEXT[kind] += 1
    return nid

# ---------------- Forms ----------------
class ProductForm(Form):
    name = StringField("Наименование", [validators.InputRequired()])
    sku = StringField("Артикул", [validators.InputRequired()])
    category = StringField("Категория", [validators.Optional()])
    unit = StringField("Ед. измерения", [validators.InputRequired()])
    supplier = SelectField("Поставщик", coerce=int)
    description = TextAreaField("Характеристики", [validators.Optional()])

class SupplierForm(Form):
    name = StringField("Название", [validators.InputRequired()])
    contact = TextAreaField("Контактная информация", [validators.Optional()])

class OperationForm(Form):
    product_id = SelectField("Товар", coerce=int)
    op_type = SelectField("Тип операции", choices=[("in","Приход"),("out","Расход"),("adjust","Списание"),("move","Перемещение")])
    quantity = IntegerField("Количество", [validators.InputRequired(), validators.NumberRange(min=1)])
    date = DateField("Дата", format="%Y-%m-%d", default=datetime.today)
    from_warehouse = StringField("Откуда (склад)", [validators.Optional()])
    to_warehouse = StringField("Куда (склад)", [validators.Optional()])
    responsible = StringField("Ответственный", [validators.Optional()])
    note = TextAreaField("Примечание", [validators.Optional()])

# ---------------- Utilities ----------------
def create_supplier(name, contact=""):
    sid = _next_id("supplier")
    DB["suppliers"][sid] = {"id": sid, "name": name, "contact": contact}
    return sid

def create_product(name, sku, category, unit, supplier_id=None, description=""):
    pid = _next_id("product")
    DB["products"][pid] = {"id": pid, "name": name, "sku": sku, "category": category, "unit": unit,
                           "supplier_id": supplier_id, "description": description}
    DB["stocks"][pid] = {"product_id": pid, "quantity": 0, "min_stock": 0, "warehouse": "Основной"}
    return pid

def add_operation(product_id, op_type, quantity, date=None, from_wh=None, to_wh=None, responsible=None, note=None):
    oid = _next_id("operation")
    op_date = date if isinstance(date, datetime) else (datetime.combine(date, datetime.min.time()) if hasattr(date, "isoformat") else (date or datetime.now()))
    op = {"id": oid, "product_id": product_id, "type": op_type, "quantity": quantity, "date": op_date,
          "from_wh": from_wh, "to_wh": to_wh, "responsible": responsible, "note": note}
    DB["operations"].append(op)
    # Обновление остатков (упрощённо)
    stock = DB["stocks"].get(product_id)
    if not stock:
        stock = {"product_id": product_id, "quantity": 0, "min_stock": 0, "warehouse": "Основной"}
        DB["stocks"][product_id] = stock
    if op_type == "in":
        stock["quantity"] += quantity
    elif op_type == "out":
        stock["quantity"] -= quantity
    elif op_type == "adjust":
        stock["quantity"] -= quantity
    elif op_type == "move":
        # В заглушке перемещения не меняют общий остаток; можно логировать from/to
        pass
    return op

# ---------------- Seed data ----------------
def seed():
    if DB["suppliers"]:
        return
    s1 = create_supplier('ООО "Поставщик-1"', 'Тел: +7 900 000 00 01')
    s2 = create_supplier('ИП Иванов', 'email: ivanov@example.com')
    p1 = create_product('Гайка М8', 'G8-001', 'Метизы', 'шт', s1, 'сталь')
    p2 = create_product('Болт М10', 'B10-002', 'Метизы', 'шт', s1, '')
    p3 = create_product('Клей ПВА', 'KL-PVA', 'Клеи', 'шт', s2, '')
    DB["stocks"][p1]["quantity"] = 100; DB["stocks"][p1]["min_stock"] = 20
    DB["stocks"][p2]["quantity"] = 5;   DB["stocks"][p2]["min_stock"] = 10
    DB["stocks"][p3]["quantity"] = 50;  DB["stocks"][p3]["min_stock"] = 5
    add_operation(p1, "in", 100, datetime(2025,1,10), responsible="Склад-1", note="Начальный приход")
    add_operation(p2, "in", 5, datetime(2025,1,11), responsible="Склад-1")
    add_operation(p3, "in", 50, datetime(2025,2,5), responsible="Склад-1")

# ---------------- Routes ----------------
@app.route("/")
def index():
    seed()
    total_products = len(DB["products"])
    total_suppliers = len(DB["suppliers"])
    low_count = sum(1 for s in DB["stocks"].values() if s.get("min_stock",0) and s["quantity"] <= s["min_stock"])
    return render_template("index.html", total_products=total_products, total_suppliers=total_suppliers, low_count=low_count)

@app.route("/products")
def product_list():
    seed()
    q = request.args.get("q","").strip()
    category = request.args.get("category","").strip()
    supplier = request.args.get("supplier","").strip()
    results = []
    for p in DB["products"].values():
        ok = True
        if q:
            if q.lower() not in p["name"].lower() and q.lower() not in p["sku"].lower():
                ok = False
        if category and category.lower() not in (p.get("category") or "").lower():
            ok = False
        if supplier:
            try:
                sid = int(supplier)
                if p.get("supplier_id") != sid:
                    ok = False
            except ValueError:
                ok = False
        if ok:
            stock = DB["stocks"].get(p["id"], {"quantity":0, "min_stock":0})
            pp = copy.deepcopy(p)
            pp.update({"stock_quantity": stock["quantity"], "min_stock": stock.get("min_stock",0), "supplier": DB["suppliers"].get(p.get("supplier_id"))})
            results.append(pp)
    # простая пагинация
    page = max(1, int(request.args.get("page", "1")))
    per_page = 20
    total = len(results)
    start = (page-1)*per_page
    return render_template("product_list.html", products=results[start:start+per_page], total=total, page=page, per_page=per_page, suppliers=DB["suppliers"].values())

@app.route("/product/add", methods=["GET","POST"])
def add_product_view():
    seed()
    form = ProductForm(request.form)
    form.supplier.choices = [(0, "---")] + [(s["id"], s["name"]) for s in DB["suppliers"].values()]
    if request.method == "POST" and form.validate():
        sup = form.supplier.data or 0
        supplier_id = None if sup == 0 else sup
        create_product(form.name.data, form.sku.data, form.category.data, form.unit.data, supplier_id, form.description.data)
        flash("Товар добавлен", "success")
        return redirect(url_for("product_list"))
    return render_template("add_product.html", form=form)

@app.route("/suppliers")
def suppliers_list():
    seed()
    return render_template("suppliers_list.html", suppliers=DB["suppliers"].values())

@app.route("/supplier/add", methods=["GET","POST"])
def add_supplier_view():
    form = SupplierForm(request.form)
    if request.method == "POST" and form.validate():
        create_supplier(form.name.data, form.contact.data)
        flash("Поставщик добавлен", "success")
        return redirect(url_for("suppliers_list"))
    return render_template("add_supplier.html", form=form)

@app.route("/operations")
def operations_list():
    seed()
    df = request.args.get("from", "")
    dt = request.args.get("to", "")
    ops = DB["operations"][:]
    def inside(op):
        if df:
            try:
                dfrom = datetime.strptime(df, "%Y-%m-%d")
                if op["date"] < dfrom: return False
            except: pass
        if dt:
            try:
                dto = datetime.strptime(dt, "%Y-%m-%d")
                if op["date"] > dto: return False
            except: pass
        return True
    ops = [o for o in ops if inside(o)]
    display = []
    for o in sorted(ops, key=lambda x: x["date"], reverse=True):
        prod = DB["products"].get(o["product_id"])
        display.append({"id": o["id"], "product": prod, "type": o["type"], "quantity": o["quantity"], "date": o["date"], "responsible": o.get("responsible"), "note": o.get("note")})
    return render_template("operations_list.html", operations=display)

@app.route("/operations/add", methods=["GET","POST"])
def add_operation_view():
    seed()
    form = OperationForm(request.form)
    form.product_id.choices = [(p["id"], f'{p["name"]} ({p["sku"]})') for p in DB["products"].values()]
    if request.method == "POST" and form.validate():
        add_operation(form.product_id.data, form.op_type.data, form.quantity.data, form.date.data, form.from_warehouse.data, form.to_warehouse.data, form.responsible.data, form.note.data)
        flash("Операция добавлена", "success")
        return redirect(url_for("operations_list"))
    return render_template("add_operation.html", form=form)

@app.route("/deliveries")
def deliveries_by_date():
    seed()
    qdate = request.args.get("date","")
    deliveries = []
    if qdate:
        try:
            d = datetime.strptime(qdate, "%Y-%m-%d").date()
            for o in DB["operations"]:
                if o["type"] == "in" and o["date"].date() == d:
                    deliveries.append({"op": o, "product": DB["products"].get(o["product_id"])})
        except ValueError:
            flash("Неверный формат даты, используйте YYYY-MM-DD", "danger")
    return render_template("operations_by_date.html", deliveries=deliveries)

@app.route("/stock/low")
def stock_low():
    seed()
    low = []
    for pid, s in DB["stocks"].items():
        if s.get("min_stock", 0) and s["quantity"] <= s["min_stock"]:
            p = copy.deepcopy(DB["products"][pid])
            p.update({"stock_quantity": s["quantity"], "min_stock": s["min_stock"], "supplier": DB["suppliers"].get(DB["products"][pid].get("supplier_id"))})
            low.append(p)
    return render_template("stock_low.html", products=low)

@app.route("/view_db")
def view_db():
    seed()
    # ВНИМАНИЕ: маршрут для отладки; в продакшене закрыть
    return render_template("view_db.html", db=DB)

if __name__ == "__main__":
    seed()
    app.run(debug=True)
