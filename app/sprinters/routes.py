from flask import Blueprint, render_template
from app.models import Sprinter

sprinters_bp = Blueprint("sprinters", __name__, url_prefix="/sprinters")

@sprinters_bp.route("/", methods=["GET"])
def index():
    sprinters = Sprinter.query.all()
    return render_template("sprinters.html", sprinters=sprinters)
