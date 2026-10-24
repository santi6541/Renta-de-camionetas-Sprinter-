from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Chofer
from app.security import roles_required

choferes_bp = Blueprint("choferes", __name__, url_prefix="/choferes")
ACCESS = ("administrador", "operaciones")
STATUSES = ("disponible", "ocupado", "descanso", "vacaciones")


@choferes_bp.route("/")
@roles_required(*ACCESS)
def index():
    choferes = Chofer.query.order_by(Chofer.apellidos, Chofer.nombre).all()
    return render_template("choferes/index.html", choferes=choferes)


@choferes_bp.route("/nuevo", methods=["GET", "POST"])
@roles_required(*ACCESS)
def create():
    if request.method == "POST":
        try:
            rate = Decimal(request.form.get("tarifa_dia", ""))
        except InvalidOperation:
            rate = Decimal("0")
        nombre = request.form.get("nombre", "").strip()
        apellidos = request.form.get("apellidos", "").strip()
        licencia = request.form.get("licencia", "").strip().upper()
        telefono = request.form.get("telefono", "").strip()
        status = request.form.get("disponibilidad", "disponible")
        if not all((nombre, apellidos, licencia, telefono)) or not rate.is_finite() or rate <= 0:
            flash("Completa los datos del chofer y una tarifa diaria válida.", "danger")
        elif status not in STATUSES:
            flash("Estado de disponibilidad no válido.", "danger")
        elif Chofer.query.filter_by(licencia=licencia).first():
            flash("La licencia ya está registrada.", "danger")
        else:
            db.session.add(
                Chofer(
                    nombre=nombre,
                    apellidos=apellidos,
                    licencia=licencia,
                    telefono=telefono,
                    disponibilidad=status,
                    tarifa_dia=rate,
                )
            )
            db.session.commit()
            flash("Chofer registrado.", "success")
            return redirect(url_for("choferes.index"))
    return render_template("choferes/form.html", chofer=None, statuses=STATUSES)


@choferes_bp.route("/<int:chofer_id>/editar", methods=["GET", "POST"])
@roles_required(*ACCESS)
def edit(chofer_id):
    chofer = db.get_or_404(Chofer, chofer_id)
    if request.method == "POST":
        try:
            rate = Decimal(request.form.get("tarifa_dia", ""))
        except InvalidOperation:
            rate = Decimal("0")
        licencia = request.form.get("licencia", "").strip().upper()
        status = request.form.get("disponibilidad", "disponible")
        duplicate = Chofer.query.filter(
            Chofer.id != chofer.id, Chofer.licencia == licencia
        ).first()
        if not all(
            request.form.get(key, "").strip()
            for key in ("nombre", "apellidos", "telefono")
        ) or not licencia or not rate.is_finite() or rate <= 0:
            flash("Completa los datos del chofer y una tarifa diaria válida.", "danger")
        elif status not in STATUSES:
            flash("Estado de disponibilidad no válido.", "danger")
        elif duplicate:
            flash("La licencia ya está registrada en otro chofer.", "danger")
        else:
            chofer.nombre = request.form["nombre"].strip()
            chofer.apellidos = request.form["apellidos"].strip()
            chofer.licencia = licencia
            chofer.telefono = request.form["telefono"].strip()
            chofer.disponibilidad = status
            chofer.tarifa_dia = rate
            db.session.commit()
            flash("Chofer actualizado.", "success")
            return redirect(url_for("choferes.index"))
    return render_template("choferes/form.html", chofer=chofer, statuses=STATUSES)
