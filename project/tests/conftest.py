from datetime import datetime, timedelta, timezone
from typing import Any, Generator, Iterator

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy

from project.app import create_app
from project.app.models import Client, ClientParking, Parking
from project.config import Config
from project.database import db as _db


@pytest.fixture(scope="module")
def app() -> Generator[Flask, Any, None]:
    class TestConfig(Config):
        TESTING = True
        WTF_CSRF_ENABLED = False
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    test_config = TestConfig()
    app = create_app(test_config)

    with app.app_context():
        _db.create_all()

        client = Client(
            name="Test",
            surname="User",
            car_number="A123BC123",
            credit_card="1234567812345678",
        )
        _db.session.add(client)

        parking = Parking(
            address="Test Address",
            opened=True,
            count_places=10,
            count_available_places=10,
        )
        _db.session.add(parking)

        log_completed = ClientParking(
            client_id=1,
            parking_id=1,
            time_in=datetime.now(timezone.utc) - timedelta(hours=1),
            time_out=datetime.now(timezone.utc),
        )
        _db.session.add(log_completed)

        log_active = ClientParking(
            client_id=1, parking_id=1, time_in=datetime.now(timezone.utc)
        )
        _db.session.add(log_active)

        _db.session.commit()

    yield app

    with app.app_context():
        _db.drop_all()


@pytest.fixture(scope="module")
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture(scope="function")
def db(app: Flask) -> Iterator[SQLAlchemy]:
    with app.app_context():
        _db.session.begin_nested()
        yield _db
        _db.session.rollback()
