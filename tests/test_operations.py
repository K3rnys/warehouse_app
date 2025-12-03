from models import db, Operation, Stock
from datetime import datetime, timedelta


def test_add_operation_increase_stock(client, sample_data):
    p = sample_data["product"]

    client.post("/operations/add", data={
        "product_id": p.id,
        "type": "in",
        "quantity": 5,
        "date": "2025-01-01"
    })

    stock = Stock.query.filter_by(product_id=p.id).first()
    assert stock.quantity == 15  # 10 + 5


def test_add_operation_out_decrease_stock(client, sample_data):
    p = sample_data["product"]

    client.post("/operations/add", data={
        "product_id": p.id,
        "type": "out",
        "quantity": 3,
        "date": "2025-01-01"
    })

    stock = Stock.query.filter_by(product_id=p.id).first()
    assert stock.quantity == 7  # 10 - 3


def test_add_operation_adjust(client, sample_data):
    p = sample_data["product"]

    client.post("/operations/add", data={
        "product_id": p.id,
        "type": "adjust",
        "quantity": 2,
        "date": "2025-01-01"
    })

    stock = Stock.query.filter_by(product_id=p.id).first()
    assert stock.quantity == 8  # 10 - 2 (твоя логика)


def test_operation_list_shown(client, sample_data):
    p = sample_data["product"]

    op = Operation(
        product_id=p.id,
        type="in",
        quantity=1,
        date=datetime.utcnow()
    )
    db.session.add(op)
    db.session.commit()

    resp = client.get("/operations")
    assert b"in" in resp.data


def test_operation_filter_by_date(client, sample_data):
    p = sample_data["product"]

    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)

    op_old = Operation(product_id=p.id, type="in", quantity=1, date=datetime(yesterday.year, yesterday.month, yesterday.day))
    op_new = Operation(product_id=p.id, type="in", quantity=2, date=datetime(today.year, today.month, today.day))

    db.session.add_all([op_old, op_new])
    db.session.commit()

    resp = client.get(f"/operations?from={today}")
    html = resp.get_data(as_text=True)
    
    # Check that the new operation (quantity 2) is present
    assert str(op_new.quantity) in html
    # Check that the old operation is NOT in the filtered results
    # by verifying op_old.id is not in the table rows
    assert f"<td>{op_old.id}</td>" not in html
