from flask import Blueprint, flash, redirect, render_template, request, url_for

from app import db
from app.models import Cliente
from app.security import roles_required

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")
ACCESS = ("administrador", "ventas", "operaciones")


@clientes_bp.route("/")
@roles_required(*ACCESS)
def index():
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    return render_template("clientes/index.html", clientes=clientes)


@clientes_bp.route("/nuevo", methods=["GET", "POST"])
@roles_required(*ACCESS)
def create():
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        email = request.form.get("email", "").strip().lower()
        rfc = request.form.get("rfc", "").strip().upper() or None
        tipo_cliente = request.form.get("tipo_cliente", "particular")
        if not nombre or not telefono or "@" not in email:
            flash("Nombre, teléfono y un correo válido son obligatorios.", "danger")
        elif tipo_cliente not in ("particular", "empresa"):
            flash("Selecciona un tipo de cliente válido.", "danger")
        else:
            db.session.add(
                Cliente(
                    nombre=nombre,
                    telefono=telefono,
                    email=email,
                    rfc=rfc,
                    tipo_cliente=tipo_cliente,
                )
            )
            db.session.commit()
            flash("Cliente registrado.", "success")
            return redirect(url_for("clientes.index"))
    return render_template("clientes/form.html", cliente=None)


@clientes_bp.route("/<int:cliente_id>/editar", methods=["GET", "POST"])
@roles_required(*ACCESS)
def edit(cliente_id):
    cliente = db.get_or_404(Cliente, cliente_id)
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        telefono = request.form.get("telefono", "").strip()
        email = request.form.get("email", "").strip().lower()
        tipo_cliente = request.form.get("tipo_cliente", "particular")
        if not nombre or not telefono or "@" not in email:
            flash("Nombre, teléfono y un correo válido son obligatorios.", "danger")
        elif tipo_cliente not in ("particular", "empresa"):
            flash("Selecciona un tipo de cliente válido.", "danger")
        else:
            cliente.nombre = nombre
            cliente.telefono = telefono
            cliente.email = email
            cliente.rfc = request.form.get("rfc", "").strip().upper() or None
            cliente.tipo_cliente = tipo_cliente
            db.session.commit()
            flash("Cliente actualizado.", "success")
            return redirect(url_for("clientes.index"))
    return render_template("clientes/form.html", cliente=cliente)


@clientes_bp.route("/<int:cliente_id>/estado", methods=["POST"])
@roles_required("administrador", "ventas")
def toggle_status(cliente_id):
    cliente = db.get_or_404(Cliente, cliente_id)
    cliente.activo = not cliente.activo
    db.session.commit()
    flash("Estado del cliente actualizado.", "success")
    return redirect(url_for("clientes.index"))
