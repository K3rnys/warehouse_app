from models import db, Operation
from datetime import datetime


def test_supplies_by_date(client, sample_data):
    p = sample_data["product"]

    op1 = Operation(
        product_id=p.id,
        type="in",
        quantity=10,
        date=datetime(2024, 1, 10)
    )
    op2 = Operation(
        product_id=p.id,
        type="out",
        quantity=5,
        date=datetime(2024, 1, 10)
    )
    db.session.add_all([op1, op2])
    db.session.commit()

    resp = client.get("/operations?from=2024-01-10&to=2024-01-10")

    assert b"10" in resp.data   # приход
    assert b"5" in resp.data    # расход
