from flask import Blueprint, jsonify, request

from app.models import Chofer, Reserva, Unidad
from app.reservas.routes import RESERVED_STATUSES, _parse_datetime
from app.security import roles_required

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/reservas")
@roles_required("administrador", "operaciones", "ventas")
def reservations():
    query = Reserva.query.order_by(Reserva.fecha_salida)
    if request.args.get("desde"):
        start = _parse_datetime(request.args["desde"])
        if not start:
            return jsonify(error="El parámetro 'desde' debe ser una fecha ISO válida."), 400
        query = query.filter(Reserva.fecha_salida >= start)
    if request.args.get("hasta"):
        end = _parse_datetime(request.args["hasta"])
        if not end:
            return jsonify(error="El parámetro 'hasta' debe ser una fecha ISO válida."), 400
        query = query.filter(Reserva.fecha_salida <= end)
    return jsonify(
        [
            {
                "folio": item.folio,
                "cliente": item.cliente.nombre,
                "unidad": item.unidad.placas,
                "chofer": f"{item.chofer.nombre} {item.chofer.apellidos}",
                "salida": item.fecha_salida.isoformat(),
                "regreso": item.fecha_regreso.isoformat(),
                "estatus": item.estatus,
                "precio_total": float(item.precio_total),
            }
            for item in query.limit(500).all()
        ]
    )


@api_bp.route("/unidades/disponibles")
@roles_required("administrador", "operaciones", "ventas")
def available_units():
    start = _parse_datetime(request.args.get("desde"))
    end = _parse_datetime(request.args.get("hasta"))
    if not start or not end or end <= start:
        return jsonify(error="Envía 'desde' y 'hasta' como fechas ISO; 'hasta' debe ser posterior."), 400

    busy_ids = {
        reservation.unidad_id
        for reservation in Reserva.query.filter(
            Reserva.estatus.in_(RESERVED_STATUSES),
            Reserva.fecha_salida < end,
            Reserva.fecha_regreso > start,
        ).all()
    }
    drivers_available = {
        reservation.chofer_id
        for reservation in Reserva.query.filter(
            Reserva.estatus.in_(RESERVED_STATUSES),
            Reserva.fecha_salida < end,
            Reserva.fecha_regreso > start,
        ).all()
    }
    units = Unidad.query.filter_by(estatus="disponible").order_by(Unidad.codigo).all()
    drivers = Chofer.query.filter_by(disponibilidad="disponible").order_by(Chofer.apellidos).all()
    return jsonify(
        {
            "unidades": [
                {
                    "id": unit.id,
                    "codigo": unit.codigo,
                    "placas": unit.placas,
                    "modelo": unit.modelo,
                    "capacidad_pasajeros": unit.capacidad_pasajeros,
                }
                for unit in units
                if unit.id not in busy_ids
            ],
            "choferes": [
                {
                    "id": driver.id,
                    "nombre": f"{driver.nombre} {driver.apellidos}",
                }
                for driver in drivers
                if driver.id not in drivers_available
            ],
        }
    )
