from datetime import datetime
from db import db


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)


class Tyre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(120), nullable=False)
    model = db.Column(db.String(120), nullable=False)
    size = db.Column(db.String(120), nullable=False)
    season = db.Column(db.String(20), nullable=False)
    studded = db.Column(db.Boolean, default=False)
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, default=0.0)
    location_id = db.Column(db.Integer, db.ForeignKey("location.id"), nullable=True)
    location = db.relationship("Location", backref="tyres")
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tyre_id = db.Column(db.Integer, db.ForeignKey("tyre.id"), nullable=False)
    tyre = db.relationship("Tyre", backref="sales")
    quantity = db.Column(db.Integer, nullable=False)
    price_per = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

