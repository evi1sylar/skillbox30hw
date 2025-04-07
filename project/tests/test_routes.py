from datetime import datetime, timezone

import pytest
from app.models import Client, ClientParking, Parking
from tests.factories import ClientFactory, ParkingFactory


@pytest.mark.parametrize(
    "route,expected",
    [
        ("/", 200),
        ("/clients", 200),
        ("/clients/1", 200),
        ("/parkings", 200),
        ("/client_parkings/active", 200),
        ("/client_parkings/exit", 200),
    ],
)
def test_get_routes(client, route, expected):
    response = client.get(route)
    assert response.status_code == expected


def test_create_client(client, db):
    test_car_number = "A123BC123"

    data = {
        "name": "New",
        "surname": "Client",
        "car_number": test_car_number,
        "credit_card": "9876543210987654",
    }

    initial_count = Client.query.count()

    response = client.post(
        "/clients/new",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert Client.query.count() == initial_count + 1

    client_db = Client.query.filter_by(name="New", surname="Client").first()
    assert client_db is not None
    assert client_db.car_number == test_car_number
    assert "Клиент успешно создан" in response.data.decode("utf-8")


def test_create_parking(client, db):
    data = {"address": "New Parking Address", "count_places": "5", "opened": "on"}
    response = client.post("/parkings/new", data=data, follow_redirects=True)
    assert response.status_code == 200

    parking = Parking.query.filter_by(address="New Parking Address").first()
    assert parking is not None
    assert parking.count_places == 5
    assert parking.opened is True


@pytest.mark.parking
def test_enter_parking(client, db):
    new_client = Client(name="Parking", surname="Test", car_number="B456DF456")
    db.session.add(new_client)
    db.session.commit()

    data = {"client_id": new_client.id, "parking_id": 1}
    response = client.post("/client_parkings/enter", data=data, follow_redirects=True)
    assert response.status_code == 200

    parking = Parking.query.get(1)
    assert parking.count_available_places == 9

    session = ClientParking.query.filter_by(
        client_id=new_client.id, parking_id=1, time_out=None
    ).first()
    assert session is not None


@pytest.mark.parking
def test_exit_parking(client, db):
    active_session = ClientParking.query.filter_by(time_out=None).first()
    assert active_session is not None

    response = client.delete(
        "/api/client_parkings/exit",
        json={
            "client_id": active_session.client_id,
            "parking_id": active_session.parking_id,
        },
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert b"success" in response.data

    parking = Parking.query.get(active_session.parking_id)
    assert parking.count_available_places == 10

    session = ClientParking.query.get(active_session.id)
    assert session.time_out is not None


@pytest.mark.parking
def test_exit_parking_no_card(client, db):
    no_card_client = Client(name="NoCard", surname="Client", car_number="C789GH789")
    db.session.add(no_card_client)
    db.session.commit()

    session = ClientParking(
        client_id=no_card_client.id, parking_id=1, time_in=datetime.now(timezone.utc)
    )
    db.session.add(session)
    db.session.commit()

    with client.application.test_request_context():
        rules = [
            rule
            for rule in client.application.url_map.iter_rules()
            if rule.endpoint == "views.process_exit"
        ]
        assert rules, "Маршрут не найден"
        print(f"Доступные маршруты: {[rule.rule for rule in rules]}")

    response = client.delete(
        "/api/client_parkings/exit",
        json={"client_id": no_card_client.id, "parking_id": 1},
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 200


def test_enter_closed_parking(client, db):
    parking = Parking.query.get(1)
    parking.opened = False
    db.session.commit()

    data = {"client_id": 1, "parking_id": 1}
    response = client.post("/client_parkings/enter", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert "Парковка закрыта" in response.get_data(as_text=True)


def test_enter_full_parking(client, db):
    parking = Parking.query.get(1)
    parking.count_available_places = 0
    parking.opened = True
    db.session.commit()

    data = {"client_id": 1, "parking_id": 1}
    response = client.post("/client_parkings/enter", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert "Нет свободных мест" in response.get_data(as_text=True)

    @pytest.mark.parking
    def test_double_enter_parking(client, db):
        new_client = Client(name="Double", surname="Enter", car_number="D111DD111")
        db.session.add(new_client)
        db.session.commit()

        data = {"client_id": new_client.id, "parking_id": 1}
        response = client.post(
            "/client_parkings/enter", data=data, follow_redirects=True
        )
        assert response.status_code == 200
        assert "Автомобиль успешно припаркован" in response.get_data(as_text=True)

        response = client.post(
            "/client_parkings/enter", data=data, follow_redirects=True
        )
        assert response.status_code == 200
        assert "Этот клиент уже находится на парковке" in response.get_data(
            as_text=True
        )

        parking = Parking.query.get(1)
        assert parking.count_available_places == 9


def test_create_client_with_factory(client, db):
    # Генерируем тестовые данные
    test_client = ClientFactory.build()
    client_data = {
        "name": test_client.name,
        "surname": test_client.surname,
        "car_number": "А123BC123",  # Явно задаем валидный номер
        "credit_card": test_client.credit_card if test_client.credit_card else "",
    }

    response = client.post(
        "/clients/new",
        data=client_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Проверяем наличие сообщения об успехе
    response_text = response.data.decode("utf-8")
    assert "Клиент успешно создан" in response_text

    # Проверяем создание клиента в БД
    new_client = Client.query.filter_by(car_number=client_data["car_number"]).first()
    assert new_client is not None
    assert new_client.name == client_data["name"]
    assert new_client.surname == client_data["surname"]


def test_create_parking_with_factory(client, db):

    initial_count = Parking.query.count()

    test_parking = ParkingFactory.build(opened=True)
    parking_data = {
        "address": test_parking.address,
        "count_places": str(test_parking.count_places),
        "opened": "on",
    }

    response = client.post("/parkings/new", data=parking_data, follow_redirects=True)

    assert response.status_code == 200
    assert Parking.query.count() == initial_count + 1

    new_parking = Parking.query.filter_by(address=parking_data["address"]).first()
    assert new_parking is not None
    assert new_parking.count_places == test_parking.count_places
    assert new_parking.opened is True
    assert new_parking.count_available_places == test_parking.count_places
    assert "Парковка успешно создана" in response.data.decode("utf-8")
