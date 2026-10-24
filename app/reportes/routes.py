from datetime import datetime
from io import BytesIO

from flask import Blueprint, send_file, render_template
from openpyxl import Workbook

from app import db
from app.models import Pago
from app.security import roles_required

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")
ACCESS = ("administrador", "ventas")


def _monthly_totals():
    totals = {}
    for payment in Pago.query.filter_by(estatus="pagado").order_by(Pago.fecha_pago).all():
        month = payment.fecha_pago.strftime("%Y-%m")
        ingresos, count = totals.get(month, (0, 0))
        totals[month] = (ingresos + payment.monto, count + 1)
    return [(month, values[0], values[1]) for month, values in sorted(totals.items())]


@reportes_bp.route("/")
@reportes_bp.route("/financiero")
@roles_required(*ACCESS)
def financiero():
    mensual = _monthly_totals()
    return render_template(
        "reportes/financiero.html",
        mensual=mensual,
        ingresos_total=sum((row[1] for row in mensual), 0),
    )


@reportes_bp.route("/exportar/excel")
@roles_required(*ACCESS)
def export_excel():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Ingresos"
    sheet.append(["Mes", "Ingresos cobrados", "Pagos"])
    for month, ingresos, count in _monthly_totals():
        sheet.append([month, float(ingresos), count])
    sheet.freeze_panes = "A2"
    sheet.column_dimensions["A"].width = 18
    sheet.column_dimensions["B"].width = 22
    sheet.column_dimensions["C"].width = 12
    for cell in sheet["B"][1:]:
        cell.number_format = '"$"#,##0.00'

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"reporte-ingresos-{datetime.now():%Y%m%d}.xlsx",
    )
