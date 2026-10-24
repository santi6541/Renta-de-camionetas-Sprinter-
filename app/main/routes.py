from flask import Blueprint, abort, render_template
from flask_login import login_required, current_user

from app.models import Cliente, Chofer, Pago, Reserva, Unidad

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.rol == "chofer":
        reservas = Reserva.query.filter_by(chofer_id=current_user.chofer_id)
    elif current_user.rol == "cliente":
        reservas = Reserva.query.filter_by(cliente_id=current_user.cliente_id)
    else:
        reservas = Reserva.query

    return render_template(
        "dashboard.html",
        clientes_count=Cliente.query.filter_by(activo=True).count()
        if current_user.rol in ("administrador", "ventas", "operaciones")
        else None,
        unidades_count=Unidad.query.count()
        if current_user.rol in ("administrador", "operaciones")
        else None,
        choferes_count=Chofer.query.count()
        if current_user.rol in ("administrador", "operaciones")
        else None,
        reservas_count=reservas.count(),
        pendientes_count=reservas.filter(Reserva.estatus.in_(["cotizacion", "confirmada"])).count(),
        pagos_pendientes=Pago.query.filter_by(estatus="pendiente").count()
        if current_user.rol in ("administrador", "ventas")
        else None,
        recent_reservations=reservas.order_by(Reserva.fecha_salida.desc()).limit(8).all(),
    )


@main_bp.route("/mis-reservas")
@login_required
def my_reservations():
    if current_user.rol == "chofer":
        reservations = Reserva.query.filter_by(chofer_id=current_user.chofer_id)
    elif current_user.rol == "cliente":
        reservations = Reserva.query.filter_by(cliente_id=current_user.cliente_id)
    else:
        abort(404)
    return render_template(
        "reservas/mine.html",
        reservas=reservations.order_by(Reserva.fecha_salida.desc()).all(),
    )
