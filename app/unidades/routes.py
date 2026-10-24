from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Unidad
from app.security import roles_required

unidades_bp = Blueprint("unidades", __name__, url_prefix="/unidades")
ACCESS = ("administrador", "operaciones")
STATUSES = ("disponible", "ocupado", "mantenimiento", "fuera_servicio")


def _unit_values():
    try:
        anio = int(request.form.get("anio", ""))
        capacity = int(request.form.get("capacidad_pasajeros", ""))
        price = Decimal(request.form.get("precio_dia", ""))
        mileage = int(request.form.get("kilometraje", "0") or "0")
    except (ValueError, InvalidOperation):
        return None
    if (
        anio < 1990
        or anio > date.today().year + 1
        or capacity < 1
        or not price.is_finite()
        or price <= 0
        or mileage < 0
    ):
        return None
    fecha_compra = request.form.get("fecha_compra", "").strip()
    try:
        purchase_date = date.fromisoformat(fecha_compra) if fecha_compra else None
    except ValueError:
        return None
    return {
        "codigo": request.form.get("codigo", "").strip().upper(),
        "marca": request.form.get("marca", "Mercedes-Benz").strip(),
        "modelo": request.form.get("modelo", "Sprinter").strip(),
        "anio": anio,
        "placas": request.form.get("placas", "").strip().upper(),
        "capacidad_pasajeros": capacity,
        "estatus": request.form.get("estatus", "disponible"),
        "precio_dia": price,
        "fecha_compra": purchase_date,
        "kilometraje": mileage,
    }


@unidades_bp.route("/")
@roles_required(*ACCESS)
def index():
    unidades = Unidad.query.order_by(Unidad.codigo).all()
    return render_template("unidades/index.html", unidades=unidades)


@unidades_bp.route("/nueva", methods=["GET", "POST"])
@roles_required(*ACCESS)
def create():
    if request.method == "POST":
        values = _unit_values()
        if not values or not values["codigo"] or not values["placas"] or not values["modelo"]:
            flash("Revisa los campos: código, modelo, placas, capacidad, año y precio son obligatorios.", "danger")
        elif values["estatus"] not in STATUSES:
            flash("Estado de unidad no válido.", "danger")
        elif Unidad.query.filter(
            (Unidad.codigo == values["codigo"]) | (Unidad.placas == values["placas"])
        ).first():
            flash("El código o las placas ya están registrados.", "danger")
        else:
            db.session.add(Unidad(**values))
            db.session.commit()
            flash("Unidad registrada.", "success")
            return redirect(url_for("unidades.index"))
    return render_template("unidades/form.html", unidad=None, statuses=STATUSES)


@unidades_bp.route("/<int:unidad_id>/editar", methods=["GET", "POST"])
@roles_required(*ACCESS)
def edit(unidad_id):
    unidad = db.get_or_404(Unidad, unidad_id)
    if request.method == "POST":
        values = _unit_values()
        duplicate = Unidad.query.filter(
            Unidad.id != unidad.id,
            (Unidad.codigo == (values or {}).get("codigo"))
            | (Unidad.placas == (values or {}).get("placas")),
        ).first()
        if not values or not values["codigo"] or not values["placas"] or not values["modelo"]:
            flash("Revisa los campos obligatorios y los valores numéricos.", "danger")
        elif values["estatus"] not in STATUSES:
            flash("Estado de unidad no válido.", "danger")
        elif duplicate:
            flash("El código o las placas ya están registrados en otra unidad.", "danger")
        else:
            for key, value in values.items():
                setattr(unidad, key, value)
            db.session.commit()
            flash("Unidad actualizada.", "success")
            return redirect(url_for("unidades.index"))
    return render_template("unidades/form.html", unidad=unidad, statuses=STATUSES)
