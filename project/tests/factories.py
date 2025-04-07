import factory
from app.models import Client, Parking
from database import db as _db
from factory.fuzzy import FuzzyChoice, FuzzyInteger, FuzzyText


class ClientFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Client
        sqlalchemy_session = _db.session

    name = factory.Faker("first_name")
    surname = factory.Faker("last_name")
    car_number = factory.Sequence(lambda n: f"А{n:03}BC{10+n:02}")  # Пример: А001BC11
    credit_card = factory.LazyAttribute(
        lambda x: (
            None
            if factory.Faker("boolean").evaluate(None, None, {"locale": None})
            else factory.Faker("credit_card_number").evaluate(
                None, None, {"locale": None}
            )
        )
    )


class ParkingFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Parking
        sqlalchemy_session = _db.session

    address = factory.Faker("street_address")
    opened = True
    count_places = FuzzyInteger(5, 50)
    count_available_places = factory.LazyAttribute(lambda o: o.count_places)
