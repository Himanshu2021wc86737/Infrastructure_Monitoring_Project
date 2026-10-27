import os
from flask import Flask
from .db import init_db

def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "local-dev-key"
    )
    app.config["DATABASE"] = "infrastructure.db"

    init_db(app)

    from .routes import bp
    app.register_blueprint(bp)

    return app