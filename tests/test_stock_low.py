from models import Stock


def test_stock_low_list(client, sample_data):
    stock = sample_data["stock"]
    stock.quantity = 3    # ниже min_stock = 5
    stock.min_stock = 5
    stock.save = False

    from models import db
    db.session.commit()

    resp = client.get("/stock/low")
    html = resp.get_data(as_text=True)
    assert "Тест Товар" in html
