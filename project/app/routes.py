import re
from datetime import datetime, timezone
from typing import List, Tuple, Union, cast

from flask import (
    Blueprint,
    Response,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.wrappers import Response as WerkzeugResponse

from project.app.models import Client, ClientParking, Parking
from project.config import Config
from project.database import db

bp = Blueprint("views", __name__)
ResponseType = Union[Response, WerkzeugResponse, str]


def validate_car_number(car_number: str) -> bool:
    pattern = r"^[АВЕКМНОРСТУХABEKMHOPCTYX]\d{3}[АВЕКМНОРСТУХABEKMHOPCTYX]{2}\d{2,3}$"
    return re.match(pattern, car_number.upper()) is not None


@bp.route("/")
def index() -> str:
    parkings_count = Parking.query.count()
    active_sessions_count = ClientParking.query.filter_by(time_out=None).count()
    return render_template(
        "index.html",
        parkings_count=parkings_count,
        active_sessions_count=active_sessions_count,
    )


@bp.route("/clients")
def list_clients() -> str:
    clients = Client.query.all()
    return render_template("clients/list.html", clients=clients)


@bp.route("/clients/<int:client_id>")
def view_client(client_id: int) -> str:
    client = Client.query.get_or_404(client_id)
    return render_template("clients/view.html", client=client)


@bp.route("/clients/new", methods=["GET", "POST"])
def create_client() -> Union[ResponseType, str]:
    if request.method == "POST":
        try:
            name = request.form["name"].strip()
            surname = request.form["surname"].strip()
            car_number = request.form["car_number"].strip()
            credit_card = request.form.get("credit_card", "").strip()

            if not name or not surname:
                flash("Имя и фамилия обязательны для заполнения", "danger")
                return render_template("clients/new.html")

            if not validate_car_number(car_number):
                flash("Неверный формат номера автомобиля", "danger")
                return render_template("clients/new.html")

            client = Client(
                name=name,
                surname=surname,
                car_number=car_number,
                credit_card=credit_card,
            )
            db.session.add(client)
            db.session.commit()

            flash("Клиент успешно создан", "success")
            return redirect(url_for("views.list_clients"))

        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка при создании клиента: {str(e)}", "danger")

    return render_template("clients/new.html")


@bp.route("/parkings")
def list_parkings() -> str:
    parkings = Parking.query.all()
    return render_template("parkings/list.html", parkings=parkings)


@bp.route("/parkings/new", methods=["GET", "POST"])
def create_parking() -> Union[ResponseType, str]:
    if request.method == "POST":
        try:
            address = request.form["address"].strip()
            count_places_str = request.form["count_places"].strip()

            if not address:
                flash("Адрес обязателен для заполнения", "danger")
                return render_template("parkings/new.html")

            try:
                count_places = int(count_places_str)
                if count_places <= 0:
                    raise ValueError
            except ValueError:
                flash("Количество мест должно быть положительным числом", "danger")
                return render_template("parkings/new.html")

            parking = Parking(
                address=address,
                count_places=count_places,
                count_available_places=count_places,
                opened="opened" in request.form,
            )
            db.session.add(parking)
            db.session.commit()
            flash("Парковка успешно создана", "success")
            return redirect(url_for("views.list_parkings"))
        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка при создании парковки: {str(e)}", "danger")

    return render_template("parkings/new.html")


@bp.route("/client_parkings/enter", methods=["GET", "POST"])
def enter_parking() -> Union[ResponseType, str]:
    if request.method == "POST":
        try:
            client_id = int(request.form["client_id"])
            parking_id = int(request.form["parking_id"])

            if ClientParking.query.filter_by(
                client_id=client_id, time_out=None
            ).first():
                flash("Этот клиент уже находится на парковке", "danger")
                return redirect(url_for("views.enter_parking"))

            parking = Parking.query.get_or_404(parking_id)

            if not parking.opened:
                flash("Парковка закрыта", "danger")
                return redirect(url_for("views.enter_parking"))

            if parking.count_available_places <= 0:
                flash("Нет свободных мест", "danger")
                return redirect(url_for("views.enter_parking"))

            log = ClientParking(
                client_id=client_id,
                parking_id=parking_id,
                time_in=datetime.now(timezone.utc),
            )
            parking.count_available_places -= 1

            db.session.add(log)
            db.session.commit()

            flash("Автомобиль успешно припаркован", "success")
            active_ids = [
                s.client_id for s in ClientParking.query.filter_by(time_out=None).all()
            ]
            return render_template(
                "client_parkings/enter.html",
                clients=Client.query.filter(~Client.id.in_(active_ids)).all(),
                parkings=Parking.query.filter(
                    Parking.opened.is_(True), Parking.count_available_places > 0
                ).all(),
            )

        except Exception as e:
            db.session.rollback()
            flash(f"Ошибка: {str(e)}", "danger")
            return redirect(url_for("views.enter_parking"))

    active_client_ids = [
        s.client_id for s in ClientParking.query.filter_by(time_out=None).all()
    ]
    available_clients = Client.query.filter(~Client.id.in_(active_client_ids)).all()
    available_parkings = Parking.query.filter(
        Parking.opened.is_(True), Parking.count_available_places > 0
    ).all()

    return render_template(
        "client_parkings/enter.html",
        clients=available_clients,
        parkings=available_parkings,
    )


def get_active_sessions() -> List[ClientParking]:
    sessions = (
        ClientParking.query.filter_by(time_out=None)
        .options(
            db.joinedload(ClientParking.client), db.joinedload(ClientParking.parking)
        )
        .all()
    )
    return cast(List[ClientParking], sessions)


@bp.route("/api/client_parkings/exit", methods=["DELETE"])
def process_exit() -> Union[Response, Tuple[Response, int]]:
    try:
        data = request.get_json()
        if not data or "client_id" not in data or "parking_id" not in data:
            return jsonify({"error": "Неверные данные запроса"}), 400

        parking_session = ClientParking.query.filter_by(
            client_id=data["client_id"], parking_id=data["parking_id"], time_out=None
        ).first()

        if not parking_session:
            return jsonify({"error": "Активная сессия не найдена"}), 404

        if parking_session.time_out:
            return jsonify({"error": "Эта сессия уже завершена"}), 400

        if "credit_card" in data and data["credit_card"]:
            parking_session.client.credit_card = data["credit_card"]
            db.session.commit()

        if not parking_session.client.credit_card:
            return (
                jsonify(
                    {
                        "require_credit_card": True,
                        "client_name": parking_session.client.name,
                        "car_number": parking_session.client.car_number,
                        "client_id": parking_session.client_id,
                        "parking_id": parking_session.parking_id,
                    }
                ),
                200,
            )

        parking_session.time_out = datetime.now(timezone.utc)
        parking_session.parking.count_available_places += 1
        db.session.commit()

        minutes = int(
            (parking_session.time_out - parking_session.time_in).total_seconds() / 60
        )
        amount = minutes * Config.PARKING_RATE_PER_MINUTE

        return jsonify(
            {"success": f"Автомобиль покинул парковку. Снята плата - {amount} руб."}
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Ошибка: {str(e)}"}), 500


@bp.route("/client_parkings/exit", methods=["GET"])
def exit_parking() -> str:
    if "_flashes" in session:
        session.pop("_flashes")

    error = request.args.get("error")
    success = request.args.get("success")

    if error:
        flash(error, "danger")
    elif success:
        flash(success, "success")

    active_sessions = (
        ClientParking.query.filter_by(time_out=None)
        .options(
            db.joinedload(ClientParking.client), db.joinedload(ClientParking.parking)
        )
        .all()
    )
    return render_template("client_parkings/exit.html", active_sessions=active_sessions)


@bp.route("/client_parkings/active")
def list_active_sessions() -> str:
    active_sessions = (
        ClientParking.query.filter_by(time_out=None)
        .options(
            db.joinedload(ClientParking.client), db.joinedload(ClientParking.parking)
        )
        .all()
    )
    return render_template(
        "client_parkings/active.html", active_sessions=active_sessions
    )
