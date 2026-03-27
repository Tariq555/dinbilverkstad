from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db():
    from models import Tyre, Location, Sale  # noqa: F401
    db.create_all()

