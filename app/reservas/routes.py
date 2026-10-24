from datetime import datetime
from decimal import Decimal, ROUND_CEILING
import secrets

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import or_

from app import db
from app.models import Chofer, Cliente, Reserva, Unidad
from app.security import roles_required

reservas_bp = Blueprint("reservas", __name__, url_prefix="/reservas")
ACCESS = ("administrador", "operaciones", "ventas")
STATUSES = ("cotizacion", "confirmada", "en_curso", "completada", "cancelada")
RESERVED_STATUSES = ("confirmada", "en_curso")


def _parse_datetime(value):
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _conflicts(unidad_id, chofer_id, start, end, exclude_id=None):
    query = Reserva.query.filter(
        Reserva.estatus.in_(RESERVED_STATUSES),
        Reserva.fecha_salida < end,
        Reserva.fecha_regreso > start,
        or_(Reserva.unidad_id == unidad_id, Reserva.chofer_id == chofer_id),
    )
    if exclude_id is not None:
        query = query.filter(Reserva.id != exclude_id)
    return query.first()


def _total_price(unidad, chofer, start, end):
    days = max(
        1,
        int(
            (
                Decimal(str((end - start).total_seconds()))
                / Decimal("86400")
            ).to_integral_value(rounding=ROUND_CEILING)
        ),
    )
    return (
        Decimal(unidad.precio_dia) + Decimal(chofer.tarifa_dia)
    ) * days


@reservas_bp.route("/")
@roles_required(*ACCESS)
def index():
    reservas = Reserva.query.order_by(Reserva.fecha_salida.desc()).all()
    return render_template("reservas/index.html", reservas=reservas, statuses=STATUSES)


@reservas_bp.route("/nueva", methods=["GET", "POST"])
@roles_required(*ACCESS)
def create():
    clientes = Cliente.query.filter_by(activo=True).order_by(Cliente.nombre).all()
    unidades = Unidad.query.filter_by(estatus="disponible").order_by(Unidad.codigo).all()
    choferes = Chofer.query.filter_by(disponibilidad="disponible").order_by(Chofer.apellidos).all()
    if request.method == "POST":
        try:
            cliente = db.get_or_404(Cliente, int(request.form.get("cliente_id", "")))
            unidad = db.get_or_404(Unidad, int(request.form.get("unidad_id", "")))
            chofer = db.get_or_404(Chofer, int(request.form.get("chofer_id", "")))
        except ValueError:
            flash("Selecciona un cliente, unidad y chofer válidos.", "danger")
            return render_template(
                "reservas/form.html",
                clientes=clientes,
                unidades=unidades,
                choferes=choferes,
            )

        start = _parse_datetime(request.form.get("fecha_salida"))
        end = _parse_datetime(request.form.get("fecha_regreso"))
        status = request.form.get("estatus", "confirmada")
        if not start or not end or end <= start:
            flash("La fecha de regreso debe ser posterior a la fecha de salida.", "danger")
        elif not cliente.activo or unidad.estatus != "disponible":
            flash("El cliente debe estar activo y la unidad disponible.", "danger")
        elif chofer.disponibilidad != "disponible":
            flash("El chofer seleccionado no está disponible.", "danger")
        elif status not in ("cotizacion", "confirmada"):
            flash("El estado inicial debe ser cotización o confirmada.", "danger")
        elif status == "confirmada" and _conflicts(unidad.id, chofer.id, start, end):
            flash("La unidad o el chofer ya tiene una reserva en esas fechas.", "danger")
        else:
            reserva = Reserva(
                folio=f"R-{datetime.now():%y%m%d}-{secrets.token_hex(3).upper()}",
                cliente=cliente,
                unidad=unidad,
                chofer=chofer,
                fecha_salida=start,
                fecha_regreso=end,
                origen=request.form.get("origen", "").strip(),
                destino=request.form.get("destino", "").strip(),
                estatus=status,
                precio_total=_total_price(unidad, chofer, start, end),
                notas=request.form.get("notas", "").strip() or None,
            )
            if not reserva.origen or not reserva.destino:
                flash("Indica el origen y el destino del viaje.", "danger")
            else:
                db.session.add(reserva)
                db.session.commit()
                flash(f"Reserva {reserva.folio} creada.", "success")
                return redirect(url_for("reservas.index"))

    return render_template(
        "reservas/form.html",
        clientes=clientes,
        unidades=unidades,
        choferes=choferes,
    )


@reservas_bp.route("/<int:reserva_id>/estado", methods=["POST"])
@roles_required("administrador", "operaciones", "ventas")
def change_status(reserva_id):
    reserva = db.get_or_404(Reserva, reserva_id)
    status = request.form.get("estatus", "")
    transitions = {
        "cotizacion": {"confirmada", "cancelada"},
        "confirmada": {"en_curso", "cancelada"},
        "en_curso": {"completada"},
        "completada": set(),
        "cancelada": set(),
    }
    if status not in transitions.get(reserva.estatus, set()):
        flash("Ese cambio de estado no está permitido.", "danger")
    elif status == "confirmada" and (
        reserva.unidad.estatus != "disponible"
        or reserva.chofer.disponibilidad != "disponible"
        or _conflicts(
            reserva.unidad_id,
            reserva.chofer_id,
            reserva.fecha_salida,
            reserva.fecha_regreso,
            reserva.id,
        )
    ):
        flash("No se puede confirmar: la unidad o el chofer no están disponibles.", "danger")
    else:
        reserva.estatus = status
        db.session.commit()
        flash("Estado de la reserva actualizado.", "success")
    return redirect(url_for("reservas.index"))
