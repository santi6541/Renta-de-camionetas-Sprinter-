from flask import Blueprint, render_template, request, redirect, url_for
from app import db
from app.models import Cliente

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")

@clientes_bp.route("/", methods=["GET"])
def index():
    clientes = Cliente.query.all()
    return render_template("clientes.html", clientes=clientes)

@clientes_bp.route("/create", methods=["POST"])
def create():
    nombre = request.form.get("nombre")
    telefono = request.form.get("telefono")
    correo = request.form.get("correo")
    nuevo = Cliente(nombre=nombre, telefono=telefono, correo=correo)
    db.session.add(nuevo)
    db.session.commit()
    return redirect(url_for("clientes.index"))
