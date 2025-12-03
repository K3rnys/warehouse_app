from models import db, Product, Stock, Supplier


def test_add_product(client, app):
    resp = client.post("/product/add", data={
        "name": "Новый товар",
        "sku": "NEW123",
        "category": "Кат A",
        "unit": "шт",
        "description": "Описание",
        "supplier": ""
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert Product.query.filter_by(sku="NEW123").first() is not None
    assert Stock.query.filter_by(product_id=Product.query.first().id).first() is not None


def test_product_search_by_name(client, sample_data):
    resp = client.get("/products?q=Тест")
    html = resp.get_data(as_text=True)
    assert "Тест Товар" in html


def test_product_search_by_category(client, sample_data):
    resp = client.get("/products?category=Категория")
    html = resp.get_data(as_text=True)
    assert "Тест Товар" in html


def test_product_search_by_supplier(client, sample_data):
    supplier_id = sample_data["supplier"].id
    resp = client.get(f"/products?supplier={supplier_id}")
    html = resp.get_data(as_text=True)
    assert "Тест Товар" in html
