from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from project.database import db


class Client(db.Model):  # type: ignore[name-defined]
    __tablename__ = "client"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    surname: Mapped[str] = mapped_column(String(50), nullable=False)
    credit_card: Mapped[Optional[str]] = mapped_column(String(50))
    car_number: Mapped[str] = mapped_column(String(10))

    parking_sessions: Mapped[list["ClientParking"]] = relationship(
        "ClientParking", back_populates="client"
    )


class Parking(db.Model):  # type: ignore[name-defined]
    __tablename__ = "parking"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    address: Mapped[str] = mapped_column(String(100), nullable=False)
    opened: Mapped[bool] = mapped_column(Boolean)
    count_places: Mapped[int] = mapped_column(Integer, nullable=False)
    count_available_places: Mapped[int] = mapped_column(Integer, nullable=False)

    parking_sessions: Mapped[list["ClientParking"]] = relationship(
        "ClientParking", back_populates="parking"
    )


class ClientParking(db.Model):  # type: ignore[name-defined]
    __tablename__ = "client_parking"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id"))
    parking_id: Mapped[int] = mapped_column(ForeignKey("parking.id"))
    time_in: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    time_out: Mapped[Optional[datetime]] = mapped_column(DateTime)

    client: Mapped["Client"] = relationship("Client", back_populates="parking_sessions")
    parking: Mapped["Parking"] = relationship(
        "Parking", back_populates="parking_sessions"
    )

    __table_args__ = ()
