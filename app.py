from flask import Flask
from config import Config
from models import db
from routes import bp

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(bp)

# Do not initialize the database at import time so tests can configure it.
# The DB will be initialized when running the app directly or by tests via
# `models.db.init_app(test_app)`.


if __name__ == "__main__":
    # Initialize DB when running the app directly
    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0', port=5000, debug=True)
