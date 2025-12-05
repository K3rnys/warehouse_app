from flask import Flask
from config import Config
from models import db
from routes import bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Инициализируем базу данных
    db.init_app(app)

    # Регистрируем blueprint
    app.register_blueprint(bp)

    return app

# Do not initialize the database at import time so tests can configure it.
# The DB will be initialized when running the app directly or by tests via
# `models.db.init_app(test_app)`.


if __name__ == "__main__":
    app = create_app()
    # Initialize DB when running the app directly
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0', port=5000, debug=True)
