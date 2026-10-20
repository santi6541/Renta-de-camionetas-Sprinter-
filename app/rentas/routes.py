from flask import Blueprint, render_template
from app.models import Renta

rentas_bp = Blueprint("rentas", __name__, url_prefix="/rentas")

@rentas_bp.route("/", methods=["GET"])
def index():
    rentas = Renta.query.all()
    return render_template("rentas.html", rentas=rentas)
