from datetime import datetime
from typing import Any, Optional

from flask import Flask

from project.app.routes import bp
from project.config import Config
from project.database import init_db


def create_app(config_class: Any = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    @app.template_filter("datetimeformat")
    def datetimeformat(
        value: Optional[datetime], format: str = "%d.%m.%Y %H:%M"
    ) -> str:
        if value is None:
            return ""
        return value.strftime(format)

    init_db(app)
    app.register_blueprint(bp)
    return app
