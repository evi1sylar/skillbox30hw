from app.routes import bp
from config import Config
from database import init_db
from flask import Flask


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    @app.template_filter("datetimeformat")
    def datetimeformat(value, format="%d.%m.%Y %H:%M"):
        if value is None:
            return ""
        return value.strftime(format)

    init_db(app)
    app.register_blueprint(bp)
    return app
