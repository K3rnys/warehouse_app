import pytest


from app import create_app
from models import db, Supplier, Product, Stock, Operation

@pytest.fixture
def app():
    flask_app = create_app()
    #flask_app = create_app()
    flask_app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })

    # Инициализируем расширение SQLAlchemy только если оно ещё не зарегистрировано
    # (иногда тестовый рантайм или импорт других модулей уже регистрировали его).
    if "sqlalchemy" not in getattr(flask_app, "extensions", {}):
        db.init_app(flask_app)

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_data(app):
    supplier = Supplier(name="Test Supplier")
    db.session.add(supplier)
    db.session.flush()

    product = Product(
        name="Тест Товар",
        sku="SKU123",
        category="Категория",
        unit="шт",
        description="Описание",
        supplier_id=supplier.id
    )
    db.session.add(product)
    db.session.flush()

    stock = Stock(product_id=product.id, quantity=10, min_stock=5)
    db.session.add(stock)
    db.session.commit()

    return {
        "supplier": supplier,
        "product": product,
        "stock": stock
    }
