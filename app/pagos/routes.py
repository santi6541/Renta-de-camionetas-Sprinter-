from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Pago, Reserva
from app.security import roles_required

pagos_bp = Blueprint("pagos", __name__, url_prefix="/pagos")
ACCESS = ("administrador", "ventas")
METHODS = ("efectivo", "transferencia", "tarjeta_credito", "paypal")
STATUSES = ("pendiente", "pagado")


@pagos_bp.route("/")
@roles_required(*ACCESS)
def index():
    pagos = Pago.query.order_by(Pago.fecha_pago.desc()).all()
    return render_template("pagos/index.html", pagos=pagos)


@pagos_bp.route("/nuevo", methods=["GET", "POST"])
@roles_required(*ACCESS)
def create():
    reservas = Reserva.query.filter(Reserva.estatus != "cancelada").order_by(Reserva.folio).all()
    if request.method == "POST":
        try:
            reserva_id = int(request.form.get("reserva_id", ""))
            monto = Decimal(request.form.get("monto", ""))
        except (ValueError, InvalidOperation):
            reserva_id, monto = 0, Decimal("0")
        reserva = db.session.get(Reserva, reserva_id)
        metodo = request.form.get("metodo_pago", "")
        status = request.form.get("estatus", "pendiente")
        referencia = request.form.get("referencia", "").strip() or None
        comprometido = sum(
            (
                pago.monto
                for pago in (reserva.pagos if reserva else [])
                if pago.estatus != "cancelado"
            ),
            Decimal("0.00"),
        )
        saldo = Decimal(reserva.precio_total) - comprometido if reserva else Decimal("0.00")
        if not reserva:
            flash("Selecciona una reserva válida.", "danger")
        elif not monto.is_finite() or monto <= 0 or monto > saldo:
            flash(f"El monto debe ser positivo y no exceder el saldo disponible ({saldo:.2f}).", "danger")
        elif metodo not in METHODS or status not in STATUSES:
            flash("Selecciona un método y estado de pago válidos.", "danger")
        else:
            db.session.add(
                Pago(
                    reserva=reserva,
                    monto=monto,
                    metodo_pago=metodo,
                    estatus=status,
                    referencia=referencia,
                )
            )
            db.session.commit()
            flash("Pago registrado.", "success")
            return redirect(url_for("pagos.index"))
    return render_template("pagos/form.html", reservas=reservas, methods=METHODS, statuses=STATUSES)


@pagos_bp.route("/<int:pago_id>/estado", methods=["POST"])
@roles_required("administrador", "ventas")
def change_status(pago_id):
    pago = db.get_or_404(Pago, pago_id)
    status = request.form.get("estatus", "")
    if status not in ("pendiente", "pagado", "cancelado"):
        flash("Estado de pago no válido.", "danger")
    elif status == "pagado":
        other_paid = sum(
            (
                other.monto
                for other in pago.reserva.pagos
                if other.id != pago.id and other.estatus == "pagado"
            ),
            Decimal("0.00"),
        )
        if other_paid + pago.monto > Decimal(pago.reserva.precio_total):
            flash("Este pago excedería el total de la reserva.", "danger")
            return redirect(url_for("pagos.index"))
        pago.estatus = status
        db.session.commit()
        flash("Estado del pago actualizado.", "success")
    else:
        pago.estatus = status
        db.session.commit()
        flash("Estado del pago actualizado.", "success")
    return redirect(url_for("pagos.index"))
