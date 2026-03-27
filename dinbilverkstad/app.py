from flask import Flask, render_template, request, redirect, url_for, flash
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os
import socket
import threading
import webbrowser
from db import db, init_db
from models import Tyre, Location, Sale


def create_app():
    is_frozen = bool(getattr(sys, "frozen", False))

    persistent_dir = Path(sys.executable).resolve().parent if is_frozen else Path(__file__).parent
    resource_dir = Path(getattr(sys, "_MEIPASS", persistent_dir))

    base_dir = Path(__file__).parent
    template_dir = str((resource_dir if is_frozen else base_dir).joinpath("templates"))
    static_dir = str((resource_dir if is_frozen else base_dir).joinpath("static"))
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config["SECRET_KEY"] = "dev"

    override_dir = os.environ.get("DVB_DATA_DIR")
    data_root = Path(override_dir).expanduser().resolve() if override_dir else persistent_dir
    data_dir = data_root.joinpath("data")
    data_dir.mkdir(exist_ok=True, parents=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{data_dir.joinpath('dinbilverkstad.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    with app.app_context():
        init_db()

    @app.route("/")
    def index():
        total_items = db.session.query(db.func.coalesce(db.func.sum(Tyre.quantity), 0)).scalar() or 0
        distinct_models = Tyre.query.count()
        out_of_stock_count = Tyre.query.filter(Tyre.quantity <= 0).count()
        low_stock_items = (
            Tyre.query.filter(Tyre.quantity.between(1, 3))
            .order_by(Tyre.quantity.asc(), Tyre.updated_at.desc())
            .limit(6)
            .all()
        )

        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7)

        sales_today_qty = (
            db.session.query(db.func.coalesce(db.func.sum(Sale.quantity), 0))
            .filter(Sale.created_at >= today_start)
            .scalar()
            or 0
        )
        sales_today_revenue = (
            db.session.query(db.func.coalesce(db.func.sum(Sale.quantity * Sale.price_per), 0.0))
            .filter(Sale.created_at >= today_start)
            .scalar()
            or 0.0
        )

        recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(8).all()

        season_rows = (
            db.session.query(Tyre.season, db.func.coalesce(db.func.sum(Tyre.quantity), 0))
            .group_by(Tyre.season)
            .all()
        )
        season_totals = {"sommar": 0, "vinter": 0, "året runt": 0, "": 0}
        for season, qty in season_rows:
            season_totals[season or ""] = int(qty or 0)

        top_sales_week = (
            db.session.query(Tyre, db.func.sum(Sale.quantity).label("qty"))
            .join(Sale, Sale.tyre_id == Tyre.id)
            .filter(Sale.created_at >= week_start)
            .group_by(Tyre.id)
            .order_by(db.desc("qty"))
            .limit(5)
            .all()
        )

        return render_template(
            "index.html",
            total_items=total_items,
            distinct_models=distinct_models,
            out_of_stock_count=out_of_stock_count,
            low_stock_items=low_stock_items,
            sales_today_qty=sales_today_qty,
            sales_today_revenue=sales_today_revenue,
            recent_sales=recent_sales,
            season_totals=season_totals,
            top_sales_week=top_sales_week,
        )

    @app.route("/dack")
    def tyres():
        q = request.args.get("q", "").strip()
        season = request.args.get("season", "").strip()
        query = Tyre.query
        if q:
            like = f"%{q}%"
            query = query.filter(
                db.or_(
                    Tyre.brand.ilike(like),
                    Tyre.model.ilike(like),
                    Tyre.size.ilike(like),
                    Tyre.notes.ilike(like),
                )
            )
        if season:
            query = query.filter(Tyre.season == season)
        tyres = query.order_by(Tyre.created_at.desc()).all()
        return render_template("tyres_list.html", tyres=tyres, q=q, season=season)

    @app.route("/dack/ny", methods=["GET", "POST"])
    def tyre_new():
        if request.method == "POST":
            brand = request.form.get("brand", "").strip()
            model = request.form.get("model", "").strip()
            size = request.form.get("size", "").strip()
            season = request.form.get("season", "").strip()
            studded = bool(request.form.get("studded"))
            quantity = int(request.form.get("quantity", 0) or 0)
            price = float(request.form.get("price", 0) or 0)
            notes = request.form.get("notes", "").strip()
            t = Tyre(brand=brand, model=model, size=size, season=season, studded=studded, quantity=quantity, price=price, location_id=None, notes=notes)
            db.session.add(t)
            db.session.commit()
            flash("Däck tillagt", "success")
            return redirect(url_for("tyres"))
        return render_template("tyre_form.html", tyre=None)

    @app.route("/dack/<int:tyre_id>/redigera", methods=["GET", "POST"])
    def tyre_edit(tyre_id: int):
        t = Tyre.query.get_or_404(tyre_id)
        if request.method == "POST":
            t.brand = request.form.get("brand", "").strip()
            t.model = request.form.get("model", "").strip()
            t.size = request.form.get("size", "").strip()
            t.season = request.form.get("season", "").strip()
            t.studded = bool(request.form.get("studded"))
            t.quantity = int(request.form.get("quantity", 0) or 0)
            t.price = float(request.form.get("price", 0) or 0)
            t.location_id = None
            t.notes = request.form.get("notes", "").strip()
            t.updated_at = datetime.utcnow()
            db.session.commit()
            flash("Däck uppdaterat", "success")
            return redirect(url_for("tyres"))
        return render_template("tyre_form.html", tyre=t)

    @app.route("/dack/<int:tyre_id>/salg", methods=["GET", "POST"])
    def tyre_sell(tyre_id: int):
        t = Tyre.query.get_or_404(tyre_id)
        if request.method == "POST":
            qty = int(request.form.get("quantity", 0) or 0)
            price_per = float(request.form.get("price_per", 0) or 0)
            if qty <= 0 or qty > t.quantity:
                flash("Ogiltig kvantitet", "danger")
                return redirect(url_for("tyre_sell", tyre_id=tyre_id))
            sale = Sale(tyre_id=t.id, quantity=qty, price_per=price_per)
            t.quantity -= qty
            db.session.add(sale)
            db.session.commit()
            flash("Försäljning registrerad", "success")
            return redirect(url_for("tyres"))
        return render_template("sale_form.html", tyre=t)

    @app.route("/platser", methods=["GET", "POST"])
    def locations_view():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            if name:
                db.session.add(Location(name=name))
                db.session.commit()
                flash("Plats tillagd", "success")
            return redirect(url_for("locations_view"))
        locations = Location.query.order_by(Location.name.asc()).all()
        return render_template("locations.html", locations=locations)

    @app.route("/platser/<int:location_id>/radera", methods=["POST"])
    def location_delete(location_id: int):
        loc = Location.query.get_or_404(location_id)
        if Tyre.query.filter_by(location_id=loc.id).count() > 0:
            flash("Kan inte radera plats med däck kopplade", "danger")
            return redirect(url_for("locations_view"))
        db.session.delete(loc)
        db.session.commit()
        flash("Plats raderad", "success")
        return redirect(url_for("locations_view"))

    return app


app = create_app()

if __name__ == "__main__":
    is_frozen = bool(getattr(sys, "frozen", False))

    def find_port(preferred: int) -> int:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", preferred))
                return preferred
        except OSError:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", 0))
                return int(s.getsockname()[1])

    preferred_port = int(os.environ.get("PORT", "5001"))
    port = find_port(preferred_port)
    url = f"http://127.0.0.1:{port}/"

    if is_frozen or os.environ.get("AUTO_OPEN", "1") == "1":
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    app.run(host="127.0.0.1", port=port, debug=not is_frozen, use_reloader=not is_frozen)
