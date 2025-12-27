from flask import Flask
from config import Config
from models import db
from routes import bp

def create_app(config_override=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    # 🔹 применяем конфиг из тестов
    if config_override:
        app.config.update(config_override)

    db.init_app(app)
    app.register_blueprint(bp)

    return app


if __name__ == "main":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)