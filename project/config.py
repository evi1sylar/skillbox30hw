from pathlib import Path

BASE_DIR = Path(__file__).parent


class Config:
    DATABASE_PATH = BASE_DIR / "database" / "parking.db"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DATABASE_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "secret-key"
    PARKING_RATE_PER_MINUTE = 10
